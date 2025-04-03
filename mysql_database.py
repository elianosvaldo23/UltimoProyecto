import aiomysql
import asyncio
from datetime import datetime, timedelta
import json

class MySQLDatabase:
    def __init__(self, host, user, password, db, port=3306):
        self.host = host
        self.user = user
        self.password = password
        self.db = db
        self.port = port
        self.pool = None

    async def init_pool(self):
        self.pool = await aiomysql.create_pool(
            host=self.host,
            user=self.user,
            password=self.password,
            db=self.db,
            port=self.port,
            autocommit=True
        )

    async def init_database(self):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                # Tabla para usuarios y sus estados
                await cur.execute('''CREATE TABLE IF NOT EXISTS users
                    (user_id BIGINT PRIMARY KEY,
                     username VARCHAR(255),
                     join_date TIMESTAMP,
                     last_verified TIMESTAMP,
                     permissions TEXT,
                     storage_used BIGINT DEFAULT 0,
                     storage_quota BIGINT DEFAULT 0,
                     expiration_date TIMESTAMP)''')

                # Tabla para verificación de canales
                await cur.execute('''CREATE TABLE IF NOT EXISTS channel_verifications
                    (user_id BIGINT,
                     channel_id BIGINT,
                     verified_date TIMESTAMP,
                     PRIMARY KEY (user_id, channel_id))''')

                # Tabla para almacenar datos de descarga
                await cur.execute('''CREATE TABLE IF NOT EXISTS downloads
                    (user_id BIGINT,
                     file_path TEXT,
                     file_size BIGINT,
                     download_date TIMESTAMP)''')

    async def add_user(self, user_id, username):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute('''INSERT IGNORE INTO users 
                    (user_id, username, join_date) 
                    VALUES (%s, %s, %s)''', 
                    (user_id, username, datetime.now()))

    async def update_channel_verification(self, user_id, channel_id):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute('''INSERT INTO channel_verifications 
                    (user_id, channel_id, verified_date) 
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE verified_date = VALUES(verified_date)''', 
                    (user_id, channel_id, datetime.now()))

    async def is_user_verified(self, user_id, channel_id):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute('''SELECT verified_date FROM channel_verifications 
                    WHERE user_id = %s AND channel_id = %s''', 
                    (user_id, channel_id))
                result = await cur.fetchone()
                return result is not None

    async def update_user_storage(self, user_id, size):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute('''UPDATE users SET storage_used = storage_used + %s 
                    WHERE user_id = %s''', (size, user_id))

    async def get_user_storage(self, user_id):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute('SELECT storage_used FROM users WHERE user_id = %s', (user_id,))
                result = await cur.fetchone()
                return result[0] if result else 0

    async def check_user_access(self, user_id):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute('''SELECT storage_used, storage_quota, expiration_date 
                    FROM users WHERE user_id = %s''', (user_id,))
                result = await cur.fetchone()
                
                if not result:
                    return False, "Usuario no registrado"
                
                storage_used, storage_quota, expiration_date = result
                if expiration_date:
                    if expiration_date < datetime.now():
                        return False, "Acceso expirado"
                        
                if storage_quota and storage_used >= storage_quota:
                    return False, "Cuota de almacenamiento excedida"
                    
                return True, None
