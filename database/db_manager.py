import sqlite3
import datetime
import threading
from pathlib import Path

DB_NAME = "mytranslator.db"

class DatabaseManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        # Singleton: Ensure only one instance exists
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, db_path=None):
        if hasattr(self, '_initialized') and self._initialized:
            return

        self.db_path = db_path if db_path else DB_NAME
        # Persistent Connection with thread check disabled for Worker access
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor_lock = threading.Lock()
        
        self.init_db()
        self._initialized = True

    def __del__(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()

    def init_db(self):
        with self.cursor_lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    original_text TEXT,
                    translated_text TEXT,
                    mode TEXT
                )
            ''')
            # Performance Index
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_original_text ON history(original_text)')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dictionary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    context TEXT,
                    term TEXT UNIQUE,
                    definition TEXT
                )
            ''')
            self.conn.commit()

    def add_history(self, original, translated, mode):
        with self.cursor_lock:
            try:
                self.conn.execute('''
                    INSERT INTO history (timestamp, original_text, translated_text, mode)
                    VALUES (?, ?, ?, ?)
                ''', (datetime.datetime.now(), original, translated, mode))
                self.conn.commit()
            except Exception as e:
                print(f"DB Error (add_history): {e}")

    def get_translation(self, original_text, mode):
        with self.cursor_lock:
            cursor = self.conn.execute('''
                SELECT translated_text 
                FROM history 
                WHERE original_text = ? AND mode = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            ''', (original_text, mode))
            row = cursor.fetchone()
            if row:
                return {"translation": row['translated_text'], "terms": []}
            return None

    def add_term(self, term, definition, context="General"):
        with self.cursor_lock:
            try:
                self.conn.execute('INSERT INTO dictionary (context, term, definition) VALUES (?, ?, ?)', (context, term, definition))
                self.conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False 
            except Exception:
                return False

    def get_all_terms(self):
        with self.cursor_lock:
            cursor = self.conn.execute('SELECT * FROM dictionary ORDER BY term')
            return [dict(row) for row in cursor.fetchall()]

    def get_history(self, limit=50):
        with self.cursor_lock:
            cursor = self.conn.execute('SELECT * FROM history ORDER BY timestamp DESC LIMIT ?', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def delete_term(self, term_id):
        with self.cursor_lock:
            self.conn.execute('DELETE FROM dictionary WHERE id = ?', (term_id,))
            self.conn.commit()
