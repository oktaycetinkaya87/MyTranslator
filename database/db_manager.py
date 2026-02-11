import sqlite3
import logging
import os

# RapidFuzz kontrolü (Varsa kullanır, yoksa hata vermez)
try:
    from rapidfuzz import process, fuzz
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False

class DatabaseManager:
    def __init__(self, db_name="mytranslator.db"):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(base_dir, db_name)
        self.init_db()

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = self.connect()
        cursor = conn.cursor()
        
        # 1. GEÇMİŞ TABLOSU
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_text TEXT NOT NULL,
                translation TEXT NOT NULL,
                style TEXT DEFAULT 'Academic',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_original_text ON history(original_text);')

        # 2. AYARLAR TABLOSU (YENİ EKLENDİ) ⚙️
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        # Varsayılan hassasiyet ayarını ekle (5 = Orta)
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('shake_sensitivity', '5')")
        
        conn.commit()
        conn.close()

    # --- AYARLARI OKU/YAZ FONKSİYONLARI ---
    def get_setting(self, key, default=None):
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row['value'] if row else default
        except Exception:
            return default
        finally:
            conn.close()

    def set_setting(self, key, value):
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value)))
            conn.commit()
        except Exception as e:
            logging.error(f"Setting Error: {e}")
        finally:
            conn.close()

    # --- MEVCUT FONKSİYONLAR (AYNEN KORUNDU) ---
    def add_history(self, original, translation, style="Academic"):
        if not original or not translation: return
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO history (original_text, translation, style) VALUES (?, ?, ?)', (original, translation, style))
            conn.commit()
        finally: conn.close()

    def get_translation(self, text, style="Academic", threshold=90):
        if not text: return None
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM history WHERE original_text = ? ORDER BY timestamp DESC LIMIT 1', (text,))
            row = cursor.fetchone()
            if row: return dict(row)
            
            # RapidFuzz (Akıllı Eşleşme)
            if RAPIDFUZZ_AVAILABLE:
                cursor.execute('SELECT original_text, translation FROM history')
                all_records = cursor.fetchall()
                choices = [rec['original_text'] for rec in all_records]
                if not choices: return None
                match = process.extractOne(text, choices, scorer=fuzz.ratio)
                if match:
                    best_match_text, score, index = match
                    if score >= threshold:
                        return {"original_text": best_match_text, "translation": all_records[index]['translation']}
            return None
        finally: conn.close()

    def get_last_history(self, limit=100):
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM history ORDER BY timestamp DESC LIMIT ?', (limit,))
            return [dict(row) for row in cursor.fetchall()]
        finally: conn.close()
        
    def get_history(self, limit=100): return self.get_last_history(limit)

    def clear_history(self):
        """Tüm çeviri geçmişini VERİTABANINDAN kalıcı olarak siler."""
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM history") # Tüm satırları sil
            # cursor.execute("DELETE FROM sqlite_sequence WHERE name='history'") # Auto-increment'i sıfırla (Opsiyonel)
            conn.commit()
            logging.info("🧹 History table cleared completely.")
        except Exception as e:
            logging.error(f"Clear History Error: {e}")
        finally:
            conn.close()
