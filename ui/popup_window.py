from PyQt6.QtWidgets import QMainWindow, QTextEdit, QVBoxLayout, QWidget, QLabel, QSplitter, QProgressBar, QApplication, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QCursor, QTextCursor, QIcon

class TranslationPopup(QMainWindow):
    def __init__(self):
        super().__init__()
        # Config: Tool (Space-independent), No StaysOnTop (Allow backgrounding)
        self.setWindowFlags(
            Qt.WindowType.Tool | 
            Qt.WindowType.WindowTitleHint | 
            Qt.WindowType.WindowCloseButtonHint | 
            Qt.WindowType.WindowSystemMenuHint
        )
        self.setWindowTitle("MyTranslator")
        self.resize(500, 450)
        self.initUI()

    def initUI(self):
        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: #FFFFFF;")
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)

        # --- HEADER (History Button) ---
        header_layout = QHBoxLayout()
        header_layout.addStretch()
        
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
                font-family: "Segoe UI Emoji";
            }
            QPushButton:hover { background-color: #e0e0e0; }
        """)
        self.history_btn.clicked.connect(self.open_history)
        header_layout.addWidget(self.history_btn)
        
        layout.addLayout(header_layout)

        # PROGRESS BAR (UX Improvement)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0) # Indeterminate mode
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setStyleSheet("QProgressBar {border: 0px; background-color: #f0f0f0;} QProgressBar::chunk {background-color: #007AFF;}")
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # SPLITTER
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setHandleWidth(8)
        splitter.setStyleSheet("QSplitter::handle { background-color: #dcdcdc; border-radius: 4px; }")

        self.original_text = QTextEdit()
        self.original_text.setReadOnly(True)
        self.original_text.setStyleSheet("border: none; color: #555; font-size: 13px; background: transparent;")
        
        self.translated_text = QTextEdit()
        self.translated_text.setReadOnly(True)
        self.translated_text.setStyleSheet("border: none; color: #000; font-size: 16px; background: transparent;")
        
        # --- COPY BUTTON (Floating) ---
        self.copy_btn = QPushButton(self.translated_text)
        self.copy_btn.setIcon(QIcon("assets/copy_icon_transparent.png"))
        self.copy_btn.setIconSize(QSize(28, 28))
        self.copy_btn.setFixedSize(40, 40)
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
        self.copy_btn.hide() # Hide initially until text available

        splitter.addWidget(self.original_text)
        splitter.addWidget(self.translated_text)
        splitter.setSizes([100, 300])

        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: red; font-size: 10px;")
        layout.addWidget(splitter)
        layout.addWidget(self.info_label)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Reposition floating button
        if hasattr(self, 'copy_btn') and hasattr(self, 'translated_text'):
            # Top Right of translated_text, with some margin
            # mapFromGlobal logic not needed since parent is translated_text
            self.copy_btn.move(
                self.translated_text.width() - self.copy_btn.width() - 5,
                5
            )

    def copy_translation(self):
        text = self.translated_text.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.copy_btn.setToolTip("Kopyalandı! ✅")
            # Restore tooltip after 1sec
            QTimer.singleShot(1000, lambda: self.copy_btn.setToolTip("Çeviriyi Kopyala"))

    def start_loading(self):
        self.progress_bar.show()
        self.original_text.setText("Veri alınıyor...")
        self.translated_text.clear()
        self.copy_btn.hide()

    def stop_loading(self):
        self.progress_bar.hide()
        if self.translated_text.toPlainText():
            self.copy_btn.show() # Show copy btn when text ready

    def append_text(self, chunk):
        """
        OPTIMİZE EDİLMİŞ AKIŞ GÖSTERİMİ:
        Metni 'setText' ile komple değiştirmek yerine, imleci sona taşıyıp 'insertText' yapıyoruz.
        Bu sayede titreme olmaz ve performans artar.
        """
        cursor = self.translated_text.textCursor()
        
        # İmleci en sona taşı
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Yeni parçayı ekle
        cursor.insertText(chunk)
        
        # UI'daki imleci güncelle ve görünür yap (Otomatik Scroll)
        self.translated_text.setTextCursor(cursor)
        self.translated_text.ensureCursorVisible()

    def update_content(self, data):
        """
        Signal Handler:
        - None -> Start Loading
        - Dict -> Show Content (Chunk/Full)
        - Str  -> Error/Message
        """
        # 1. Loading
        if data is None:
            self.start_loading()
            if not self.isVisible():
                self.move_to_cursor_position()
                self.show()
            return
            
        # 2. Content Updates
        if isinstance(data, dict):
            # Source Text Update
            if "source_text" in data:
                self.original_text.setText(data["source_text"])

            # A. Streaming Chunk (Do NOT stop loading yet)
            if "chunk" in data:
                self.append_chunk(data["chunk"])
                return # Keep progress bar active!

            # B. Finished Signal
            if "finished" in data:
                self.stop_loading()
                if self.translated_text.toPlainText():
                    self.copy_btn.show()
                    self.copy_btn.raise_()
                return

            # C. Full Translation (Cache/Final)
            if "translation" in data:
                self.stop_loading()
                self.translated_text.setText(data["translation"])
                self.copy_btn.show()
                self.copy_btn.raise_()
                
        elif isinstance(data, str):
            self.stop_loading()
            self.translated_text.setText(data)
            self.copy_btn.show()
            self.copy_btn.raise_()

    def append_chunk(self, chunk):
        """
        SMART APPEND (Scrolsuz Ekleme):
        Kullanıcı en sonu okumuyorsa, ekranı kaydırmadan alta ekle.
        Böylece kullanıcı üst kısmı okurken altta çeviri devam eder.
        """
        scrollbar = self.translated_text.verticalScrollBar()
        was_at_bottom = (scrollbar.value() == scrollbar.maximum())
        
        # Detached Cursor ile ekle (Görünümü etkilemez)
        cursor = self.translated_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(chunk)
        
        # Eğer kullanıcı zaten en alttaysa, otomatik kaydır (Opsiyonel)
        # Kullanıcı "Kaymasın" dediği için bunu kapatıyorum veya kontrollü yapıyorum.
        # İstenirse: if was_at_bottom: scrollbar.setValue(scrollbar.maximum())
        # Amaç: Kullanıcı okurken metin zıplamasın.
        
        # İPUCU: Progress Bar yukarıda hala dönüyor, bu "Çalışıyor" hissiyatı verir.

    def move_to_cursor_position(self):
        # 1. Hide first to detach from current space
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
        self.show()
        self.raise_()
        # self.activateWindow() # Disabled to prevent Space Switching on macOS

    def open_history(self):
        from ui.history_window import HistoryWindow
        # Lazy Loading
        if not hasattr(self, 'history_window') or self.history_window is None:
            self.history_window = HistoryWindow()
        
        self.history_window.load_data()
        self.history_window.show()
        self.history_window.raise_()
        self.history_window.activateWindow()
