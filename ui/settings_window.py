from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QLabel, 
                             QSlider, QHBoxLayout, QListWidget, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from database.db_manager import DatabaseManager

class SettingsWindow(QWidget):
    def __init__(self, clipboard_handler=None):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.clipboard_handler = clipboard_handler
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Ayarlar")
        self.resize(360, 240) 
        # Modern, White Background
        self.setStyleSheet("""
            QWidget { 
                background-color: #FFFFFF; 
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
            }
        """)
        
        self.init_general_settings()

    def init_general_settings(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        # --- TITLE "Titretme (Shake) Hassasiyeti" ---
        title_box = QHBoxLayout()
        
        # Icon (Optional, removing for cleaner look or keeping minimal)
        # title_box.addWidget(icon_lbl) 
        
        title = QLabel("Titretme Hassasiyeti")
        title.setFont(QFont("Futura", 16)) # Match Main Popup
        title.setStyleSheet("color: #111; margin-bottom: 5px;")
        title_box.addWidget(title)
        title_box.addStretch()
        layout.addLayout(title_box)
        
        # --- DESCRIPTION ---
        desc = QLabel("Çeviriyi başlatmak için fareyi boşta sağa-sola sallayın.")
        desc.setStyleSheet("color: #666; font-size: 13px; line-height: 1.4;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addSpacing(10)

        # --- SLIDER CONTAINER ---
        from PyQt6.QtWidgets import QGridLayout
        grid = QGridLayout()
        grid.setSpacing(15)
        
        # Labels: Az - Çok
        self.lbl_low = QLabel("Az")
        self.lbl_low.setStyleSheet("color: #999; font-size: 12px; font-weight: 500;")
        
        self.lbl_high = QLabel("Çok") 
        self.lbl_high.setStyleSheet("color: #999; font-size: 12px; font-weight: 500;")
        
        # --- MODERN SLIDER ---
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(10)
        self.slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.slider.setFixedHeight(30)
        
        # Apple-style Slider CSS
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #E5E5E5;
                height: 6px;
                background: #F0F0F0;
                margin: 0px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #FFFFFF;
                border: 1px solid #D1D1D1;
                width: 20px;
                height: 20px;
                margin: -8px 0; /* center on groove */
                border-radius: 10px; /* circle */
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            QSlider::handle:horizontal:hover {
                border: 1px solid #B0B0B0;
                background: #FAFAFA;
            }
            QSlider::sub-page:horizontal {
                background: #007AFF; /* Apple Blue */
                border-radius: 3px;
            }
        """)
        
        # Current Value Logic
        current_val = int(self.db_manager.get_setting("shake_sensitivity", 5))
        self.slider.setValue(current_val)
        
        # --- VALUE DISPLAY (Floating Pill) ---
        self.val_label = QLabel(f"{current_val}")
        self.val_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.val_label.setFixedSize(30, 24)
        self.val_label.setFont(QFont("Futura", 14)) # Match Font
        # Pill Style
        self.val_label.setStyleSheet("""
            color: #007AFF; 
            background: rgba(0, 122, 255, 0.1); 
            border-radius: 6px; 
            font-weight: bold;
        """)
        
        # Grid Placement
        # Row 0: Az [Slider] Çok
        grid.addWidget(self.lbl_low, 0, 0, Qt.AlignmentFlag.AlignRight)
        grid.addWidget(self.slider, 0, 1)
        grid.addWidget(self.lbl_high, 0, 2, Qt.AlignmentFlag.AlignLeft)
        
        # Row 1: Value centered under slider
        grid.addWidget(self.val_label, 1, 1, Qt.AlignmentFlag.AlignCenter)
        
        layout.addLayout(grid)
        layout.addStretch()
        
        self.slider.valueChanged.connect(self.on_slider_change)
        self.setLayout(layout)

    def on_slider_change(self, value):
        self.val_label.setText(str(value))
        self.db_manager.set_setting("shake_sensitivity", value)
        if self.clipboard_handler:
            self.clipboard_handler.set_sensitivity(value)
