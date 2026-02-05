from PyQt6.QtWidgets import (
    QMainWindow, QTextEdit, QVBoxLayout, QWidget, QLabel, 
    QSplitter, QProgressBar, QApplication, QPushButton, QHBoxLayout, QFrame
)
from PyQt6.QtCore import Qt, QTimer, QSize, QEvent, pyqtSignal
from PyQt6.QtGui import QCursor, QTextCursor, QIcon, QFont, QAction
import platform
import os
import subprocess
try:
    if platform.system() == 'Darwin':
        from AppKit import NSApplication
except ImportError:
    pass

class TranslationPopup(QMainWindow):
    # Yeni Signal: Rephrase/Humanize isteği için (source_text, current_text) gönderir
    humanize_requested = pyqtSignal(str, str) 

    def __init__(self):
        super().__init__()
        
        # --- EKLENEN KISIM 1: Değişkeni Başlat ---
        self.original_translation = None 
        # ---------------------------------------

        # --- PENCERE AYARLARI (DÜZELTİLDİ) ---
        self.setWindowFlags(
            Qt.WindowType.WindowTitleHint | 
            Qt.WindowType.WindowCloseButtonHint | 
            Qt.WindowType.WindowSystemMenuHint |
            Qt.WindowType.WindowSystemMenuHint
            # Qt.WindowType.WindowStaysOnTopHint  # REMOVED per user request
        )
        self.setWindowTitle("MyTranslator")
        self.resize(500, 480) 
        self.initUI()

    def initUI(self):
        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: #FFFFFF;")
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # --- ÜST BAR (Geçmiş) ---
        top_header_layout = QHBoxLayout()
        top_header_layout.addStretch()
        
        self.history_btn = QPushButton("🕒")
        self.history_btn.setFixedSize(30, 30)
        self.history_btn.setToolTip("Geçmiş (Son 100)")
        self.history_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.history_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; 
                border-radius: 15px;
                font-size: 16px;
                color: #555;
            }
            QPushButton:hover { background-color: #e0e0e0; }
        """)
        self.history_btn.clicked.connect(self.open_history)
        top_header_layout.addWidget(self.history_btn)
        
        main_layout.addLayout(top_header_layout)

        # PROGRESS BAR
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setStyleSheet("QProgressBar {border: 0px; background-color: #f0f0f0;} QProgressBar::chunk {background-color: #007AFF;}")
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)

        # --- SPLITTER ---
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.setHandleWidth(8)
        self.splitter.setStyleSheet("QSplitter::handle { background-color: #dcdcdc; border-radius: 4px; }")

        # SCROLLBAR STİLİ
        scrollbar_style = """
            QScrollBar:vertical { width: 8px; background: #f1f1f1; border-radius: 4px; }
            QScrollBar::handle:vertical { background: #c1c1c1; border-radius: 4px; }
            QScrollBar::handle:vertical:hover { background: #a8a8a8; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """

        # 1. ÜST BÖLME
        self.original_text = QTextEdit()
        self.original_text.setReadOnly(True)
        self.original_text.setPlaceholderText("Kaynak metin...")
        self.original_text.setStyleSheet("""
            QTextEdit { border: none; color: #555; font-size: 13px; background: transparent; padding: 5px; }
        """ + scrollbar_style)
        
        # 2. ALT BÖLME (Konteyner)
        bottom_container = QWidget()
        bottom_container.setStyleSheet("background-color: transparent;") 
        
        bottom_layout = QVBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(0)

        # --- OPTİMİZE EDİLEN HEADER (40px) ---
        translation_header = QWidget()
        translation_header.setFixedHeight(40) 
        translation_header.setStyleSheet("background-color: transparent;")
        
        header_row_layout = QHBoxLayout(translation_header)
        header_row_layout.setContentsMargins(10, 0, 5, 0) 
        header_row_layout.addStretch() 
        
        # KOPYALAMA BUTONU
        self.copy_btn = QPushButton()
        self.copy_btn.setIcon(QIcon("assets/copy_icon_transparent.png"))
        self.copy_btn.setIconSize(QSize(24, 24)) 
        self.copy_btn.setFixedSize(32, 32)       
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.setToolTip("Çeviriyi Kopyala")
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; 
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: rgba(0,0,0,0.05); }
        """)
        self.copy_btn.clicked.connect(self.copy_translation)
        self.copy_btn.hide() 

        header_row_layout.addWidget(self.copy_btn)
        
        # --- ÇEVİRİ ALANI ---
        self.translated_text = QTextEdit()
        self.translated_text.setReadOnly(True)
        self.translated_text.setStyleSheet("""
            QTextEdit { 
                border: none; 
                color: #000; 
                font-size: 16px; 
                background: transparent; 
                padding: 10px;
                padding-top: 5px; 
            }
        """ + scrollbar_style)

        self.humanize_btn = QPushButton("✨") 
        self.humanize_btn.setToolTip("Humanize (Daha Doğal Yap)")
        self.humanize_btn.setFixedSize(30, 30)
        self.humanize_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.humanize_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; 
                border: none;
                border-radius: 4px;
                font-size: 18px;
            }
            QPushButton:hover { background-color: rgba(0,0,0,0.05); }
        """)
        self.humanize_btn.clicked.connect(self.on_humanize_click)
        self.humanize_btn.hide() # Başlangıçta gizli

        header_row_layout.addWidget(self.humanize_btn)
        header_row_layout.addWidget(self.copy_btn)

        bottom_layout.addWidget(translation_header)
        bottom_layout.addWidget(self.translated_text)

        self.splitter.addWidget(self.original_text)
        self.splitter.addWidget(bottom_container)
        self.splitter.setSizes([100, 350]) 

        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: red; font-size: 10px;")
        
        main_layout.addWidget(self.splitter)
        main_layout.addWidget(self.info_label)

    def copy_translation(self):
        text = self.translated_text.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.copy_btn.setToolTip("Kopyalandı! ✅")
            original_title = self.windowTitle()
            self.setWindowTitle("✅ Kopyalandı!")
            QTimer.singleShot(1000, lambda: self.reset_copy_feedback(original_title))

    def reset_copy_feedback(self, original_title):
        self.setWindowTitle(original_title)
        self.copy_btn.setToolTip("Çeviriyi Kopyala")

    def start_loading(self):
        self.progress_bar.show()
        self.original_text.setText("Veri alınıyor...")
        self.translated_text.clear()
        
        # --- EKLENEN KISIM 2: Yeni işlemde eski kaydı temizle ---
        self.original_translation = None 
        # --------------------------------------------------------

        self.copy_btn.hide()
        self.humanize_btn.hide()

    def stop_loading(self):
        self.progress_bar.hide()
        if self.translated_text.toPlainText():
            self.copy_btn.show()
            self.humanize_btn.show()

    def update_content(self, data):
        try:
            if data is None:
                self.start_loading()
                if not self.isVisible():
                    self.move_to_cursor_position()
                    self.show()
                return
                
            if isinstance(data, dict):
                if "source_text" in data:
                    self.original_text.setText(data["source_text"])
                    self.adjust_input_height()
                if "chunk" in data:
                    self.append_chunk(data["chunk"])
                elif "translation" in data:
                    self.update_text(data["translation"])
                elif "finished" in data:
                    self.stop_loading()
                    # Capture the full translation as the AUTHENTIC SOURCE
                    if self.original_translation is None:
                         self.original_translation = self.translated_text.toPlainText()
                
            elif isinstance(data, str):
                self.stop_loading()
                # Hata mesajlarını info_label'a yönlendir, ana metni kirletme
                if data.startswith("Hata:") or data.startswith("Error:") or "[Error:" in data:
                    self.info_label.setText(f"⚠️ {data}")
                    self.info_label.setStyleSheet("color: red; font-size: 11px;")
                else:
                    self.update_text(data)
        except Exception as e:
            print(f"Error in update_content: {e}")
            import traceback
            traceback.print_exc()
            
    def update_text(self, content):
        """Metni tamamen değiştirir (İlk açılışta veya temizlemede)"""
        if content is None:
            self.translated_text.clear()
        else:
            self.translated_text.setPlainText(str(content))

    def append_chunk(self, chunk):
        """Stream edilen metni ekler"""
        if not chunk: return
        try:
            cursor = self.translated_text.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertText(chunk)
            # Otomatik kaydır
            sb = self.translated_text.verticalScrollBar()
            sb.setValue(sb.maximum())
        except Exception as e:
            print(f"Error append: {e}")

    def on_humanize_click(self):
        """Humanize butonuna basılınca"""
        print("DEBUG: Humanize Button Clicked!") # Debug Log
        current_text = self.translated_text.toPlainText()
        
        # Eğer henüz orijinal kaydedilmediyse (örn. tamamlanmadan basıldıysa), şu anki hali orijinal kabul et
        source_ref = self.original_translation if self.original_translation else current_text
        
        if source_ref.strip():
            self.translated_text.setPlainText("Humanizing...") 
            # (Source Reference, Current Text) gönderilir
            self.humanize_requested.emit(source_ref, current_text)

    def adjust_input_height(self):
        doc_height = self.original_text.document().size().height()
        target_height = int(doc_height + 25) 
        total_height = self.splitter.height()
        max_allowed_height = total_height - 150
        final_height = max(60, min(target_height, max_allowed_height))
        self.splitter.setSizes([final_height, total_height - final_height])

    def move_to_cursor_position(self):
        # 1. Pencereyi mouse yanına taşı
        self.hide()
        mouse_pos = QCursor.pos()
        target_screen = QApplication.screenAt(mouse_pos) or QApplication.primaryScreen()
        
        if not self.windowHandle(): self.winId()
        if self.windowHandle(): self.windowHandle().setScreen(target_screen)
        
        geo = target_screen.availableGeometry()
        x = mouse_pos.x() + 20
        y = mouse_pos.y() + 20
        
        if x + self.width() > geo.right(): x = geo.right() - self.width() - 20
        if y + self.height() > geo.bottom(): y = geo.bottom() - self.height() - 20
        
        self.move(x, y)
        self.showNormal()
        try:
            self.raise_()
            self.activateWindow()
        except: pass

        # 2. HIZLI ODAKLANMA (MacOS Hack)
        # subprocess/osascript yerine Native API kullanıyoruz (0 Gecikme)
        if platform.system() == 'Darwin':
            try:
                NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
            except Exception as e:
                print(f"Focus Error: {e}")

    def open_history(self):
        from ui.history_window import HistoryWindow
        if not hasattr(self, 'history_window') or self.history_window is None:
            self.history_window = HistoryWindow()
        self.history_window.load_data()
        self.history_window.show()
        self.history_window.raise_()
        self.history_window.activateWindow()
