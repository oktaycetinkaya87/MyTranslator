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
        
        # --- KALAN KULLANIM HAKKI KARTI ---
        # --- KALAN KULLANIM HAKKI KARTI (COMPACT) ---
        usage_card = QWidget()
        usage_card.setStyleSheet("""
            QWidget {
                background-color: #F8F9FA;
                border: 1px solid #E9ECEF;
                border-radius: 8px;
            }
        """)
        
        # Yatay Düzen (Daha az yer kaplar)
        usage_layout = QHBoxLayout(usage_card)
        usage_layout.setContentsMargins(12, 8, 12, 8)
        usage_layout.setSpacing(10)
        
        # Kullanım bilgisini al
        if self.clipboard_handler and hasattr(self.clipboard_handler, 'usage_tracker'):
            tracker = self.clipboard_handler.usage_tracker
            remaining = tracker.get_remaining()
            
            if remaining == -1:  # Limitsiz
                # Icon
                icon_lbl = QLabel("💎")
                icon_lbl.setFont(QFont("Segoe UI Emoji", 14))
                icon_lbl.setStyleSheet("border: none; background: transparent;")
                
                # Text Container
                text_layout = QVBoxLayout()
                text_layout.setSpacing(0)
                text_layout.setContentsMargins(0, 0, 0, 0)
                
                title = QLabel("Limitsiz Erişim")
                title.setFont(QFont("Futura", 13, QFont.Weight.Bold))
                title.setStyleSheet("color: #2E7D32; border: none; background: transparent;")
                
                desc = QLabel("Hesabınızda sınır yok")
                desc.setFont(QFont("System", 11))
                desc.setStyleSheet("color: #666; border: none; background: transparent;")
                
                text_layout.addWidget(title)
                text_layout.addWidget(desc)
                
                usage_layout.addWidget(icon_lbl)
                usage_layout.addLayout(text_layout)
                usage_layout.addStretch()
                
            else:  # Limited
                # Icon
                icon_lbl = QLabel("📊")
                icon_lbl.setFont(QFont("Segoe UI Emoji", 14))
                icon_lbl.setStyleSheet("border: none; background: transparent;")
                
                # Text Container
                text_layout = QVBoxLayout()
                text_layout.setSpacing(2)
                text_layout.setContentsMargins(0, 0, 0, 0)
                
                title = QLabel("Kalan Hakkınız")
                title.setFont(QFont("Futura", 12, QFont.Weight.Bold))
                title.setStyleSheet("color: #333; border: none; background: transparent;")
                
                # Progress Bar benzeri text
                limit_text = QLabel(f"{remaining} / {tracker.limit} Çeviri")
                limit_text.setFont(QFont("System", 11))
                if remaining < 10:
                     limit_text.setStyleSheet("color: #D32F2F; border: none; background: transparent; font-weight: bold;")
                else:
                     limit_text.setStyleSheet("color: #666; border: none; background: transparent;")

                text_layout.addWidget(title)
                text_layout.addWidget(limit_text)
                
                usage_layout.addWidget(icon_lbl)
                usage_layout.addLayout(text_layout)
                usage_layout.addStretch()
        else:
            usage_title = QLabel("⚠️ Bilgi Yok")
            usage_title.setStyleSheet("color: #999; font-size: 12px; border: none;")
            usage_layout.addWidget(usage_title)
        
        layout.addWidget(usage_card)
        layout.addSpacing(10)
        
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
