from PyQt6.QtWidgets import (
    QMainWindow, QTextEdit, QVBoxLayout, QWidget, QLabel, 
    QSplitter, QProgressBar, QApplication, QPushButton, QHBoxLayout, QFrame
)
from PyQt6.QtCore import Qt, QTimer, QSize, QEvent
from PyQt6.QtGui import QCursor, QTextCursor, QIcon
import platform
import os
import subprocess

class TranslationPopup(QMainWindow):
    def __init__(self):
        super().__init__()
        # --- PENCERE AYARLARI (DÜZELTİLDİ) ---
        self.setWindowFlags(
            Qt.WindowType.WindowTitleHint | 
            Qt.WindowType.WindowCloseButtonHint | 
            Qt.WindowType.WindowSystemMenuHint |
            Qt.WindowType.WindowStaysOnTopHint  # <--- BU EKLENDİ (Öne gelme sorunu çözer)
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

        # --- OPTİMİZE EDİLEN HEADER (30px) ---
        translation_header = QWidget()
        translation_header.setFixedHeight(30) 
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
        self.copy_btn.hide()

    def stop_loading(self):
        self.progress_bar.hide()
        if self.translated_text.toPlainText():
            self.copy_btn.show()

    def update_content(self, data):
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
                return

            if "finished" in data:
                self.stop_loading()
                return

            if "translation" in data:
                self.stop_loading()
                self.translated_text.setText(data["translation"])
                
        elif isinstance(data, str):
            self.stop_loading()
            self.translated_text.setText(data)
            
    def adjust_input_height(self):
        doc_height = self.original_text.document().size().height()
        target_height = int(doc_height + 25) 
        total_height = self.splitter.height()
        max_allowed_height = total_height - 150
        final_height = max(60, min(target_height, max_allowed_height))
        self.splitter.setSizes([final_height, total_height - final_height])

    def append_chunk(self, chunk):
        cursor = self.translated_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(chunk)

    def move_to_cursor_position(self):
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
        
        try:
            self.move(x, y)
            self.showNormal()
            self.raise_()
            self.activateWindow()
            
            # MacOS force focus strategy
            if platform.system() == 'Darwin':
                try:
                    # Alternative script strategy
                    script = '''
                    tell application "System Events"
                        set procs to every process whose unix id is {}
                        if procs is not {} then
                            set frontmost of item 1 of procs to true
                        end if
                    end tell
                    '''.format(os.getpid(), "{}")
                    subprocess.run(["osascript", "-e", script], check=False)
                except Exception as e:
                    print(f"Window activation error: {e}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error in move_to_cursor_position: {e}")

    def open_history(self):
        from ui.history_window import HistoryWindow
        if not hasattr(self, 'history_window') or self.history_window is None:
            self.history_window = HistoryWindow()
        self.history_window.load_data()
        self.history_window.show()
        self.history_window.raise_()
        self.history_window.activateWindow()
