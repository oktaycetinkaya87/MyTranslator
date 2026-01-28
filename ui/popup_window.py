from PyQt6.QtWidgets import QMainWindow, QTextEdit, QVBoxLayout, QWidget, QLabel, QSplitter, QProgressBar, QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor

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

        splitter.addWidget(self.original_text)
        splitter.addWidget(self.translated_text)
        splitter.setSizes([100, 300])

        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: red; font-size: 10px;")
        layout.addWidget(splitter)
        layout.addWidget(self.info_label)

    def start_loading(self):
        self.progress_bar.show()
        self.original_text.setText("Veri alınıyor...")
        self.translated_text.clear()

    def stop_loading(self):
        self.progress_bar.hide()

    def append_text(self, chunk):
        current = self.translated_text.toPlainText()
        self.translated_text.setText(current + chunk)
        cursor = self.translated_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.translated_text.setTextCursor(cursor)

    def update_content(self, data):
        self.stop_loading()
        if not data:
            self.translated_text.setText("Çeviri hatası.")
            return
        if "translation" in data:
            self.translated_text.setText(data["translation"])
            source = data.get("source_text", "Kaynak metin yok")
            self.original_text.setText(source)
        else:
            self.translated_text.setText("Çeviri yapılamadı.")

    def move_to_cursor_position(self):
        # Smart positioning logic moved here
        mouse_pos = QCursor.pos()
        target_screen = QApplication.screenAt(mouse_pos) or QApplication.primaryScreen()
        
        # Use winId() to ensure handle exists (Fixing AttributeError: createWinId)
        if not self.windowHandle(): self.winId()
        if self.windowHandle(): self.windowHandle().setScreen(target_screen)
        
        geo = target_screen.availableGeometry()
        x = mouse_pos.x() + 20
        y = mouse_pos.y() + 20
        
        if x + self.width() > geo.right(): x = geo.right() - self.width() - 20
        if y + self.height() > geo.bottom(): y = geo.bottom() - self.height() - 20
        
        self.move(x, y)
        if self.isVisible():
            self.hide() # Detach before show
        self.show()
        self.raise_()
        self.activateWindow()
