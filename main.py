import sys
import logging
import time # <--- Added missing import
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread, pyqtSignal

# Import Core Services
from core.clipboard_handler import ClipboardListener
from core.api_service import APIService
from database.db_manager import DatabaseManager
from ui.popup_window import TranslationPopup

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# Initialize App
app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)

# --- WORKER THREAD ---
class TranslationWorker(QThread):
    stream_chunk = pyqtSignal(str)   # Signal for real-time text
    finished = pyqtSignal()          # Signal when done
    
    def __init__(self, api_service, db_manager, text):
        super().__init__()
        self.api = api_service
        self.db = db_manager
        self.text = text
        
    def run(self):
        start_t = time.time()
        try:
            # 1. Cache Check
            logging.info("🔍 [Worker] Checking Database for Smart Match...")
            db_start = time.time()
            
            cached = self.db.get_translation(self.text, "Academic")
            
            db_end = time.time()
            logging.info(f"⏱️ [Worker] DB Search took: {(db_end - db_start) * 1000:.2f} ms")

            if cached and "translation" in cached:
                logging.info(f"⚡️ Cache Hit! Score: {cached.get('match_score', '100')}")
                # Simulate stream for cache
                self.stream_chunk.emit(cached["translation"])
                self.finished.emit()
                return
            
            logging.info("❌ Cache Miss. Falling back to API...")

            # 2. API Stream
            api_start = time.time()
            full_translation = ""
            first_chunk_received = False
            
            for chunk in self.api.translate_text_stream(self.text):
                if not first_chunk_received:
                    latency = (time.time() - api_start) * 1000
                    logging.info(f"🚀 [Worker] First API Chunk received in: {latency:.2f} ms")
                    first_chunk_received = True

                if chunk:
                    full_translation += chunk
                    self.stream_chunk.emit(chunk)
            
            total_time = time.time() - start_t
            logging.info(f"✅ [Worker] Finished. Total time: {total_time:.2f}s")
            
            # 3. Save to DB (Background)
            if full_translation:
                self.db.add_history(self.text, full_translation, "Academic")
            
            self.finished.emit()
            
        except Exception as e:
            self.stream_chunk.emit(f"\n[Hata: {str(e)}]")
            self.finished.emit()

# --- DEPENDENCY INJECTION ---
try:
    handler = ClipboardListener()
    api = APIService()
    api.warmup() # <--- Connection Warmup
    db = DatabaseManager()
    popup = TranslationPopup()
    
    handler.start()

except Exception as e:
    logging.error(f"Initialization Failed: {e}")
    sys.exit(1)

import re # <--- Added re import

# ... (Logging config and Worker class remain same until dependency injection) ...

# --- LOGIC ---

def clean_text(text):
    """
    PDF VE BOZUK METİN TEMİZLEYİCİ:
    1. Satır sonundaki tireleri (-) birleştirir.
    2. Gereksiz satır başlarını (\\n) boşluğa çevirir.
    3. Fazla boşlukları tek boşluğa indirir.
    """
    if not text: return ""
    
    # 1. Tire ile ayrılmış kelimeleri birleştir (hyphenation fix)
    text = re.sub(r'-\s*\n\s*', '', text)
    
    # 2. Satır sonlarını boşlukla değiştir (paragrafı koru)
    text = text.replace('\n', ' ')
    text = text.replace('\r', ' ')
    
    # 3. Çoklu boşlukları tek boşluğa indir
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def handle_chunk_received(chunk):
    """Called on every stream packet"""
    popup.append_text(chunk)

def handle_stream_finished():
    """Called when stream ends"""
    popup.stop_loading()
    
    # Justify Translation (Final Polish)
    cursor = popup.translated_text.textCursor()
    cursor.select(cursor.SelectionType.Document)
    logging.info("✅ Stream Finished")

def handle_trigger():
    """
    Triggered ONLY by Cmd+C+C
    """
    logging.info("🎹 Keyboard Trigger Received")
    
    clipboard = QApplication.clipboard()
    raw_text = clipboard.text()
    
    if not raw_text or not raw_text.strip():
        return

    # METNİ TEMİZLE (Fix PDF Hyphenation & Spacing)
    text = clean_text(raw_text)
    logging.info(f"🧹 Cleaned Text: {text[:50]}...")

    # Reset UI
    if popup.isVisible():
        popup.hide()
        
    # Start Loading (Show Source Text Immediately)
    popup.move_to_cursor_position()
    popup.start_loading() # No args
    popup.original_text.setText(text) # Manually set source
    
    # Start Background Worker
    global worker 
    worker = TranslationWorker(api, db, text)
    worker.stream_chunk.connect(handle_chunk_received)
    worker.finished.connect(handle_stream_finished)
    worker.start()

# Connect Signal
handler.hotkey_triggered.connect(handle_trigger)

logging.info("🚀 MyTranslator Streaming Mode (Gemini 3.0 Flash Preview) Ready.")
sys.exit(app.exec())
