import sys
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal

# Import Classes
from ui.popup_window import TranslationPopup
from core.clipboard_handler import ClipboardHandler

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class SignalManager(QObject):
    """
    Bridge between non-GUI threads (pynput/worker) and GUI thread (PyQt)
    """
    update_signal = pyqtSignal(object) # Data carrier
    move_signal = pyqtSignal()         # UI Action carrier

class MainApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        self.popup = TranslationPopup()
        self.signals = SignalManager()
        
        # Connect Signals -> GUI Slots
        self.signals.update_signal.connect(self.popup.update_content)
        self.signals.move_signal.connect(self.popup.move_to_cursor_position)

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

    def run(self):
        self.clipboard_handler.start()
        logging.info("🚀 MyTranslator Architecture V2 (Signal-Based) Ready.")
        sys.exit(self.app.exec())

if __name__ == "__main__":
    MainApp().run()
