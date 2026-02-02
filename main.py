import sys
import logging
import faulthandler
# faulthandler.enable()
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal

# Import Classes
from ui.popup_window import TranslationPopup
from core.clipboard_handler import ClipboardHandler

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(threadName)s] %(message)s')

# Custom Exception Hook to prevent PyQt from crashing on unhandled errors
def exception_hook(exctype, value, traceback):
    logging.critical("Uncaught Exception", exc_info=(exctype, value, traceback))
    sys.__excepthook__(exctype, value, traceback)

sys.excepthook = exception_hook

class SignalManager(QObject):
    """
    Bridge between non-GUI threads (pynput/worker) and GUI thread (PyQt)
    """
    update_signal = pyqtSignal(object) # Data carrier
    move_signal = pyqtSignal()         # UI Action carrier
    read_clipboard_signal = pyqtSignal() # Request carrier

class MainApp(QObject):
    def __init__(self):
        super().__init__()
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        self.popup = TranslationPopup()
        self.signals = SignalManager()
        
        # Connect Signals -> GUI Slots
        self.signals.update_signal.connect(self.popup.update_content)
        self.signals.move_signal.connect(self.popup.move_to_cursor_position)
        self.signals.read_clipboard_signal.connect(self.read_system_clipboard)

        # Initialize Logic Controller
        # Pass callback methods that trigger signals
        self.clipboard_handler = ClipboardHandler(
            update_callback=self.emit_update,
            move_window_callback=self.emit_move
        )

    def emit_update(self, data):
        """Called from background thread"""
        self.signals.update_signal.emit(data)

    def emit_move(self):
        """Called from background thread"""
        self.signals.move_signal.emit()

    def emit_clipboard_read_request(self):
        """Called from background thread to request Main Thread clipboard read"""
        self.signals.read_clipboard_signal.emit()

    def read_system_clipboard(self):
        """Executes in Main Thread"""
        try:
            logging.info("📋 Main Thread: Reading Clipboard...")
            clipboard = QApplication.clipboard()
            text = clipboard.text()
            logging.info(f"📋 Read Content: {text[:50]}...")
            # Pass back to logic handler (will spawn its own thread for heavy lifting)
            self.clipboard_handler.process_clipboard_content(text)
        except Exception as e:
            logging.error(f"CRITICAL ERROR in read_system_clipboard: {e}", exc_info=True)

    def run(self):
        self.clipboard_handler.start()
        logging.info("🚀 MyTranslator Architecture V2 (Signal-Based) Ready.")
        sys.exit(self.app.exec())

if __name__ == "__main__":
    MainApp().run()
