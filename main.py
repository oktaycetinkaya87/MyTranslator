import sys
import fix_pynput
import logging
import os
import platform
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QStyle
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QObject, pyqtSignal, QLockFile, QDir, Qt

from ui.popup_window import TranslationPopup
from ui.settings_window import SettingsWindow
from core.clipboard_handler import ClipboardHandler

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

class SignalManager(QObject):
    update_signal = pyqtSignal(object) 
    move_signal = pyqtSignal()
    snip_trigger_signal = pyqtSignal() 
    open_settings_signal = pyqtSignal() 

class MainApp(QObject):
    def __init__(self):
        super().__init__()
        
        # ⭐ HIGH DPI DESTEĞİ - QApplication'dan ÖNCE
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        
        self.app = QApplication(sys.argv)
        
        
        self.app.setQuitOnLastWindowClosed(False)

        # Kilit (Tekil Çalışma)
        lock_path = os.path.join(QDir.tempPath(), 'MyTranslator.lock')
        self.lock = QLockFile(lock_path)
        if not self.lock.tryLock(100): sys.exit(0)

        # Dock'ta Gizle
        if platform.system() == 'Darwin':
            try:
                from AppKit import NSApplication, NSApplicationActivationPolicyAccessory
                NSApplication.sharedApplication().setActivationPolicy_(NSApplicationActivationPolicyAccessory)
            except: pass

        self.signals = SignalManager()
        self.popup = TranslationPopup()
        self.settings_window = None 

        # Logic Handler
        self.clipboard_handler = ClipboardHandler(
            self.signals.update_signal.emit,
            self.signals.move_signal.emit,
            self.signals.snip_trigger_signal.emit
        )

        # SİNYAL BAĞLANTILARI
        self.signals.update_signal.connect(self.popup.update_content)
        self.signals.move_signal.connect(self.popup.show_at_cursor)
        
        self.signals.snip_trigger_signal.connect(
            self.popup.start_snipping, 
            type=Qt.ConnectionType.QueuedConnection
        )
        
        self.popup.settings_requested.connect(self.open_settings)
        self.popup.humanize_requested.connect(self.clipboard_handler.process_humanize_request)
        self.popup.image_captured.connect(self.clipboard_handler.process_image)

        # System Tray Başlat
        self.init_tray()

    def init_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logging.error("❌ System Tray is not available on this system.")
            return

        self.tray = QSystemTrayIcon(self.app)
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_dir, 'assets', 'tray_ikon.png')
        
        if os.path.exists(icon_path):
            logging.info(f"✅ Tray Icon found: {icon_path}")
            
            dpr = self.app.devicePixelRatio()
            target_size = 28 
            
            pixmap = QIcon(icon_path).pixmap(int(target_size * dpr), int(target_size * dpr))
            pixmap.setDevicePixelRatio(dpr)
            
            self.tray.setIcon(QIcon(pixmap)) 
        else:
            logging.warning(f"⚠️ Tray Icon not found at {icon_path}, using default.")
            self.tray.setIcon(self.app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        
        self.tray.setVisible(True)
        
        # Menüyü Oluştur
        menu = QMenu()
        
        settings_action = menu.addAction("⚙️ Ayarlar")
        settings_action.triggered.connect(self.open_settings)
        
        snip_action = menu.addAction("📸 Ekran Çevirisi")
        snip_action.triggered.connect(self.trigger_snip_manual)
        
        menu.addSeparator()
        
        quit_action = menu.addAction("Çıkış")
        quit_action.triggered.connect(self.app.quit)
        
        self.tray.setContextMenu(menu)
        self.tray.show()

    def open_settings(self):
        if self.settings_window and self.settings_window.isVisible():
            self.settings_window.activateWindow()
            self.settings_window.raise_()
            return
            
        self.settings_window = SettingsWindow(clipboard_handler=self.clipboard_handler)
        self.settings_window.show()

    def trigger_snip_manual(self):
        self.popup.start_snipping()

    def run(self):
        self.clipboard_handler.start()
        sys.exit(self.app.exec())

if __name__ == "__main__":
    MainApp().run()
