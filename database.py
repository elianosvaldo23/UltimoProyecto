import sqlite3
from datetime import datetime
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
                     storage_used INTEGER DEFAULT 0)''')
        
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
