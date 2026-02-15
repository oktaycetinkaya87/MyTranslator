import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, 
                             QVBoxLayout, QHBoxLayout, QFrame, QLineEdit, QPushButton)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QFont, QColor, QPalette, QPainter, QPen, QBrush

class MockupOverlay(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(100, 100, 800, 500)
        
        # Ana Konteyner
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 1. ORİJİNAL EKRAN SİMÜLASYONU (Arka Plan)
        # Sanki altta bir PDF veya Web sitesi varmış gibi
        self.bg_label = QLabel(self.central_widget)
        self.bg_label.setGeometry(50, 50, 700, 400)
        self.bg_label.setStyleSheet("background-color: white; border-radius: 10px; border: 1px solid #ddd;")
        
        # Orijinal İngilizce Metin (Flu/Silik Görünecek)
        self.original_text = QLabel("The system utilizes an advanced neural network.", self.bg_label)
        self.original_text.setFont(QFont("Arial", 24))
        self.original_text.setStyleSheet("color: #ccc;") # Silik renk
        self.original_text.move(50, 100)

        # 2. ÇEVİRİ KATMANI (Overlay Boxes)
        # "utilizes" -> "kullanır"
        self.create_translation_box(260, 150, "kullanır", width=110)
        
        # "advanced" -> "gelişmiş" (Buna tıklandığını varsayacağız)
        self.active_box = self.create_translation_box(380, 150, "gelişmiş", width=130, active=True)
        
        # "neural network" -> "sinir ağı"
        self.create_translation_box(520, 150, "sinir ağı", width=140)

        # 3. BAĞLAMSAL POPUP (Token Popup)
        self.show_popup(380, 205)

    def create_translation_box(self, x, y, text, width=100, active=False):
        box = QLineEdit(self.bg_label)
        box.setText(text)
        box.setGeometry(x, y, width, 40)
        box.setFont(QFont("Segoe UI", 18))
        box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if active:
            # Düzenleme Modu (Aktif)
            box.setStyleSheet("""
                QLineEdit {
                    background-color: rgba(255, 255, 255, 0.95);
                    border: 2px solid #3b82f6;
                    border-radius: 4px;
                    color: #1e293b;
                    selection-background-color: #3b82f6;
                }
            """)
        else:
            # Normal Mod (Sadece metin gibi duruyor)
            box.setStyleSheet("""
                QLineEdit {
                    background-color: rgba(255, 240, 200, 0.6); 
                    border: none;
                    color: #000;
                }
                QLineEdit:hover {
                    background-color: rgba(255, 255, 255, 0.9);
                    border: 1px dashed #999;
                }
            """)
        return box

    def show_popup(self, x, y):
        """Token tıklandığında açılan menü"""
        popup = QFrame(self.bg_label)
        popup.setGeometry(x, y, 220, 160)
        popup.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border-radius: 8px;
                border: 1px solid #444;
                color: white;
            }
        """)
        
        layout = QVBoxLayout(popup)
        layout.setSpacing(5)
        
        # Üst Bilgi (Orijinal Kelime)
        header = QLabel("Orijinal: advanced")
        header.setStyleSheet("color: #888; font-size: 10pt; font-style: italic; border:none;")
        layout.addWidget(header)
        
        # Alternatifler Listesi
        alts = ["• ileri düzey", "• modern", "• komplike"]
        for alt in alts:
            btn = QPushButton(alt)
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    background-color: transparent;
                    color: #ddd;
                    border: none;
                    padding: 3px;
                }
                QPushButton:hover {
                    background-color: #3b82f6;
                    color: white;
                    border-radius: 3px;
                }
            """)
            layout.addWidget(btn)
            
        # Alt Bilgi (Kaydet)
        save_btn = QPushButton("💾 Hafızaya Kaydet")
        save_btn.setStyleSheet("""
            background-color: #22c55e;
            color: white;
            border-radius: 4px;
            font-weight: bold;
            padding: 5px;
            margin-top: 5px;
        """)
        layout.addWidget(save_btn)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MockupOverlay()
    window.show()
    sys.exit(app.exec())
