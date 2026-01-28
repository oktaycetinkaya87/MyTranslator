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
    finished = pyqtSignal(dict)
    
    def __init__(self, api_service, db_manager, text):
        super().__init__()
        self.api = api_service
        self.db = db_manager
        self.text = text
        
    def run(self):
        try:
            # 1. Cache Check
            cached = self.db.get_translation(self.text, "Academic")
            if cached:
                logging.info("⚡️ Cache Hit!")
                self.finished.emit(cached)
                return

            # 2. API Call
            result = self.api.translate_text(self.text)
            
            # 3. Save to DB
            if result and "translation" in result:
                self.db.add_history(self.text, result["translation"], "Academic")
            
            self.finished.emit(result)
            
        except Exception as e:
            self.finished.emit({"translation": f"Hata: {str(e)}"})

# --- DEPENDENCY INJECTION ---
# We only instantiate the necessary components for the keyboard workflow
try:
    handler = ClipboardListener()
    api = APIService()
    db = DatabaseManager()
    popup = TranslationPopup()
    
    # Start the keyboard listener thread
    handler.start()

except Exception as e:
    logging.error(f"Initialization Failed: {e}")
    sys.exit(1)

# --- LOGIC ---
def on_translation_finished(result, source_text):
    logging.info("✅ Translation Received")
    if result:
        result["source_text"] = source_text
    popup.update_content(result)

def handle_trigger():
    """
    Triggered ONLY by Cmd+C+C
    """
    logging.info("🎹 Keyboard Trigger Received")
    
    # 1. Get Text from Clipboard
    clipboard = QApplication.clipboard()
    text = clipboard.text()
    
    if not text or not text.strip():
        return

    # 2. Prepare UI (Reset & Move)
    if popup.isVisible():
        popup.hide()
        
    popup.start_loading()
    popup.move_to_cursor_position()

    # 3. Start Background Worker
    global worker 
    worker = TranslationWorker(api, db, text)
    worker.finished.connect(lambda res: on_translation_finished(res, text))
    worker.start()

# Connect Signal
handler.hotkey_triggered.connect(handle_trigger)

logging.info("🚀 MyTranslator Restored to Stable Mode (Cmd+C+C).")
sys.exit(app.exec())
