import sys
import logging
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
        try:
            # 1. Cache Check
            # Using Cache would require a different flow (return full text immediately).
            # For "HIZLI MOD" (Fast Mode), user probably wants fresh stream, but cache is faster.
            cached = self.db.get_translation(self.text, "Academic")
            if cached and "translation" in cached:
                logging.info("⚡️ Cache Hit!")
                # Simulate stream for cache (or just blast it)
                self.stream_chunk.emit(cached["translation"])
                self.finished.emit()
                return

            # 2. API Stream
            full_translation = ""
            for chunk in self.api.translate_text_stream(self.text):
                if chunk:
                    full_translation += chunk
                    self.stream_chunk.emit(chunk)
            
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
    db = DatabaseManager()
    popup = TranslationPopup()
    
    handler.start()

except Exception as e:
    logging.error(f"Initialization Failed: {e}")
    sys.exit(1)

# --- LOGIC ---
def handle_chunk_received(chunk):
    """Called on every stream packet"""
    popup.append_chunk(chunk)

def handle_stream_finished():
    """Called when stream ends"""
    popup.stop_loading()
    
    # Justify Translation (Final Polish)
    cursor = popup.translated_text.textCursor()
    cursor.select(cursor.SelectionType.Document)
    # Qt.AlignmentFlag.AlignJustify is not directly available via textCursor without block format
    # But we can try to set alignment on the widget if needed, or leave left-aligned for stream natural feel.
    logging.info("✅ Stream Finished")

def handle_trigger():
    """
    Triggered ONLY by Cmd+C+C
    """
    logging.info("🎹 Keyboard Trigger Received")
    
    clipboard = QApplication.clipboard()
    text = clipboard.text()
    
    if not text or not text.strip():
        return

    # Reset UI
    if popup.isVisible():
        popup.hide()
        
    # Start Loading (Show Source Text Immediately)
    popup.move_to_cursor_position()
    popup.start_loading(source_text=text)

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
