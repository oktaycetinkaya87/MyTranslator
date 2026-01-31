from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel, 
    QPushButton, QApplication, QMessageBox, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QIcon
from database.db_manager import DatabaseManager

class HistoryItemWidget(QFrame):
    def __init__(self, item_data):
        super().__init__()
        self.setStyleSheet("""
            HistoryItemWidget {
                background-color: white;
                border-bottom: 1px solid #eee;
                border-radius: 4px;
            }
            HistoryItemWidget:hover {
                background-color: #f5f5f5;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                color: #aaa;
                font-size: 14px;
            }
            QPushButton:hover {
                color: #007AFF;
                background-color: #e3f2fd;
                border-radius: 4px;
            }
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)
        
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        # Üst Satır: Tarih (Sol)
        timestamp = item_data['timestamp'].split('.')[0] 
        time_lbl = QLabel(f"🕒 {timestamp}")
        time_lbl.setStyleSheet("color: #888; font-size: 11px; border: none; background: transparent;")
        layout.addWidget(time_lbl)

        # Helper to create text row with copy button
        def create_text_row(text, color, style="normal"):
            row_layout = QHBoxLayout()
            row_layout.setSpacing(10) # Metin ve buton arası boşluk
            
            # Text Label
            lbl = QLabel(text)
            lbl.setStyleSheet(f"color: {color}; font-size: 13px; font-style: {style}; border: none; background: transparent;")
            lbl.setWordWrap(True)
            lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            row_layout.addWidget(lbl)
            
            # Copy Button Container (Align Top)
            btn_container = QVBoxLayout()
            btn_container.setAlignment(Qt.AlignmentFlag.AlignTop)
            btn_container.setContentsMargins(0, 0, 0, 0)
            
            copy_btn = QPushButton("") # No Text
            copy_btn.setIcon(QIcon("assets/copy_icon_transparent.png"))
            copy_btn.setIconSize(QSize(28, 28)) # Explicit size
            
            copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            copy_btn.setFixedSize(40, 40) # Larger hit area
            copy_btn.setToolTip("Kopyala")
            copy_btn.setStyleSheet("background: transparent; border: none;") 
            # Lambda fix: capture 'text' carefully
            copy_btn.clicked.connect(lambda _, t=text: self.copy_text_to_clipboard(t))
            
            btn_container.addWidget(copy_btn)
            row_layout.addLayout(btn_container)
            
            return row_layout

        # Orta Satır: Orijinal Metin
        layout.addLayout(create_text_row(item_data['original_text'], "#333"))

        # Alt Satır: Çeviri
        layout.addLayout(create_text_row(item_data['translation'], "#007AFF", "italic"))
        
        self.setLayout(layout)

    def copy_text_to_clipboard(self, text):
        QApplication.clipboard().setText(text)
        # Visual Feedback on parent window title? 
        # Since we are inside item, ideally we should signal up or find parent.
        # But User request was simple. Let's try to find parent window to update title or show tooltip.
        # For now, just copy is enough per req, but user UX is nice.
        # Let's emit a signal on the Application instance or just rely on OS feedback?
        # Re-using the window title trick requires access to window.
        window = self.window()
        if window:
            original_title = "Çeviri Geçmişi (Son 100)"
            window.setWindowTitle("✅ Kopyalandı!")
            QTimer.singleShot(1000, lambda: window.setWindowTitle(original_title))

class HistoryWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.setWindowTitle("Çeviri Geçmişi (Son 100)")
        self.resize(500, 600)
        self.setStyleSheet("background-color: #f9f9f9;")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Başlık ve Bilgi
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #fff; border-bottom: 1px solid #eee;")
        header_layout = QVBoxLayout(header_frame)
        
        title = QLabel("Son Çeviriler")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333; border: none;")
        header_layout.addWidget(title)
        
        # info label removed due to explicit copy buttons
        
        layout.addWidget(header_frame)

        # SCROLL AREA (Dynamic List)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("""
            QScrollArea { background: transparent; }
            QScrollBar:vertical { width: 8px; background: #f1f1f1; }
            QScrollBar::handle:vertical { background: #c1c1c1; border-radius: 4px; }
        """)
        
        # Container Widget inside Scroll Area
        self.container_widget = QWidget()
        self.container_widget.setStyleSheet("background-color: #f9f9f9;") # Match bg
        self.container_layout = QVBoxLayout(self.container_widget)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(0)
        self.container_layout.setAlignment(Qt.AlignmentFlag.AlignTop) # Don't stretch vertically
        
        self.scroll_area.setWidget(self.container_widget)
        layout.addWidget(self.scroll_area)

        # Alt Bar (Temizle)
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(15, 10, 15, 15)
        
        clear_btn = QPushButton("Tümünü Temizle")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff3b30; 
                color: white; 
                border-radius: 6px; 
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #d32f2f; }
        """)
        clear_btn.clicked.connect(self.clear_history)
        
        bottom_layout.addStretch()
        bottom_layout.addWidget(clear_btn)
        
        layout.addLayout(bottom_layout)
        self.setLayout(layout)
        
        # Yükle
        self.load_data()

    def load_data(self):
        # Clear existing items
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        history = self.db.get_last_history()
        
        for item_data in history:
            widget = HistoryItemWidget(item_data)
            # Signal Removed: Widget handles its own copy logic now
            self.container_layout.addWidget(widget)

    # copy_text method removed as it is handled in HistoryItemWidget

    def clear_history(self):
        reply = QMessageBox.question(self, 'Onay', 
                                     "Tüm çeviri geçmişi silinecek.\nEmin misiniz?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.db.clear_history()
            self.load_data()
