import sqlite3
from datetime import datetime
from datetime import timedelta  # Nueva línea añadida
import json

class Database:
    def __init__(self, db_file="bot_database.db"):
        self.db_file = db_file
        self.init_database()

    def init_database(self):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        # Tabla para usuarios y sus estados
        c.execute('''CREATE TABLE IF NOT EXISTS users
                    (user_id INTEGER PRIMARY KEY,
                     username TEXT,
                     join_date TIMESTAMP,
                     last_verified TIMESTAMP,
                     permissions TEXT,
                     storage_used INTEGER DEFAULT 0,
                     storage_quota INTEGER DEFAULT 0,
                     expiration_date TIMESTAMP)''')
        
        # Tabla para verificación de canales
        c.execute('''CREATE TABLE IF NOT EXISTS channel_verifications
                    (user_id INTEGER,
                     channel_id INTEGER,
                     verified_date TIMESTAMP,
                     PRIMARY KEY (user_id, channel_id))''')
        
        # Tabla para almacenar datos de descarga
        c.execute('''CREATE TABLE IF NOT EXISTS downloads
                    (user_id INTEGER,
                     file_path TEXT,
                     file_size INTEGER,
                     download_date TIMESTAMP)''')
        
        conn.commit()
        conn.close()

    def add_user(self, user_id, username):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute('''INSERT OR IGNORE INTO users 
                    (user_id, username, join_date) 
                    VALUES (?, ?, ?)''', 
                    (user_id, username, datetime.now()))
        conn.commit()
        conn.close()

    def update_channel_verification(self, user_id, channel_id):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO channel_verifications 
                    (user_id, channel_id, verified_date) 
                    VALUES (?, ?, ?)''', 
                    (user_id, channel_id, datetime.now()))
        conn.commit()
        conn.close()

    def is_user_verified(self, user_id, channel_id):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute('''SELECT verified_date FROM channel_verifications 
                    WHERE user_id = ? AND channel_id = ?''', 
                    (user_id, channel_id))
        result = c.fetchone()
        conn.close()
        return result is not None

    def update_user_storage(self, user_id, size):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute('''UPDATE users SET storage_used = storage_used + ? 
                    WHERE user_id = ?''', (size, user_id))
        conn.commit()
        conn.close()

    def get_user_storage(self, user_id):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute('SELECT storage_used FROM users WHERE user_id = ?', (user_id,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else 0

    def remove_channel_verification(self, user_id, channel_id):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute('''DELETE FROM channel_verifications 
                    WHERE user_id = ? AND channel_id = ?''', 
                    (user_id, channel_id))
        conn.commit()
        conn.close()

    def set_user_quota(self, user_id, quota_gb):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        quota_bytes = quota_gb * 1024 * 1024 * 1024
        c.execute('''UPDATE users 
                    SET storage_quota = ? 
                    WHERE user_id = ?''', (quota_bytes, user_id))
        conn.commit()
        conn.close()

    def set_expiration_date(self, user_id, days):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        expiration_date = datetime.now()
        expiration_date = expiration_date.replace(hour=23, minute=59, second=59)
        expiration_date = expiration_date + timedelta(days=days)
        c.execute('''UPDATE users 
                    SET expiration_date = ? 
                    WHERE user_id = ?''', (expiration_date, user_id))
        conn.commit()
        conn.close()

    def check_user_access(self, user_id):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute('''SELECT storage_used, storage_quota, expiration_date 
                    FROM users WHERE user_id = ?''', (user_id,))
        result = c.fetchone()
        conn.close()
        
        if not result:
            return False, "Usuario no registrado"
            
        storage_used, storage_quota, expiration_date = result
        if expiration_date:
            try:
                if datetime.strptime(expiration_date, '%Y-%m-%d %H:%M:%S') < datetime.now():
                    return False, "Acceso expirado"
            except:
                pass
                
        if storage_quota and storage_used >= storage_quota:
            return False, "Cuota de almacenamiento excedida"
            
        return True, None
