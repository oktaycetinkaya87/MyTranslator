import sqlite3
import json
import logging
from datetime import datetime
import os

# Akıllı Eşleşme Kontrolü
try:
    from rapidfuzz import process, fuzz
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False
    logging.warning("⚠️ RapidFuzz bulunamadı. Akıllı eşleşme devre dışı.")

class DatabaseManager:
    def __init__(self, db_name="mytranslator.db"):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(base_dir, db_name)
        self.init_db()

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        # PERFORMANS AYARI: WAL Modu (Eşzamanlı okuma/yazma)
        conn.execute("PRAGMA journal_mode=WAL;") 
        conn.execute("PRAGMA synchronous=NORMAL;") # Disk yazma güvenliğini koruyarak hızı artırır
        return conn

    def init_db(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_text TEXT NOT NULL,
                translation TEXT NOT NULL,
                style TEXT DEFAULT 'Academic',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # HIZLI ARAMA İÇİN İNDEKS (Performansın sırrı buradadır)
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_original_text ON history(original_text);')
        conn.commit()
        conn.close()

    def add_history(self, original, translation, style="Academic"):
        if not original or not translation: return
        conn = self.connect()
        try:
            cursor = conn.cursor()
            # Önce var mı diye bak (Index sayesinde çok hızlı)
            cursor.execute('SELECT id FROM history WHERE original_text = ? AND style = ?', (original, style))
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute('UPDATE history SET translation = ?, timestamp = CURRENT_TIMESTAMP WHERE id = ?', (translation, existing[0]))
            else:
                cursor.execute('INSERT INTO history (original_text, translation, style) VALUES (?, ?, ?)', (original, translation, style))
            conn.commit()
            logging.info(f"💾 [DB] Kaydedildi.")
        except Exception as e:
            logging.error(f"DB Error: {e}")
        finally:
            conn.close()

    def get_translation(self, text, style="Academic", threshold=90):
        if not text: return None
        conn = self.connect()
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            # 1. Tam Eşleşme (Index Kullanır - 0ms)
            cursor.execute('SELECT * FROM history WHERE original_text = ? AND style = ? ORDER BY timestamp DESC LIMIT 1', (text, style))
            row = cursor.fetchone()
            if row:
                logging.info("⚡️ [DB] Tam Eşleşme!")
                return dict(row)

            # 2. Akıllı Eşleşme (RapidFuzz)
            if RAPIDFUZZ_AVAILABLE:
                cursor.execute('SELECT original_text, translation FROM history WHERE style = ?', (style,))
                all_records = cursor.fetchall()
                choices = [rec['original_text'] for rec in all_records]
                
                if not choices: return None

                match = process.extractOne(text, choices, scorer=fuzz.ratio)
                if match:
                    best_match_text, score, index = match
                    if score >= threshold:
                        logging.info(f"🧠 [DB] Akıllı Eşleşme (%{score:.1f})")
                        return {
                            "original_text": best_match_text,
                            "translation": all_records[index]['translation'],
                            "match_score": score,
                            "match_type": "fuzzy"
                        }
            return None
        except Exception as e:
            logging.error(f"DB Get Error: {e}")
            return None
        finally:
            conn.close()
            
    def clear_history(self):
        conn = self.connect()
        conn.execute('DELETE FROM history')
        conn.commit()
        conn.close()

    def get_last_history(self, limit=100):
        conn = self.connect()
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM history ORDER BY timestamp DESC LIMIT ?', (limit,))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"DB History Error: {e}")
            return []
        finally:
            conn.close()
