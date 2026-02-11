from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QRect, pyqtSignal, QBuffer, QIODevice
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush

class SnippingTool(QWidget):
    snippet_taken = pyqtSignal(object) 

    def __init__(self):
        super().__init__()
        # MacOS için Tool yerine Window kullanmak bazen daha stabildir
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background-color: black;")
        self.setWindowOpacity(0.3)
        self.begin = None
        self.end = None
        self.is_snipping = False
        self.first_click_released = False # İLK tıklama bırakıldı mı?

    def start(self):
        # Tüm ekranların toplam geometriğini hesapla (Virtual Desktop)
        total_rect = QRect()
        for screen in QApplication.screens():
            total_rect = total_rect.united(screen.geometry())
        
        self.setGeometry(total_rect)
        self.first_click_released = False # Sıfırla
        
        # Pencereyi göster ve EN ÖNE getir
        self.show()
        self.raise_()
        self.activateWindow()
        
        # İmleci ZORLA değiştir (Override)
        QApplication.setOverrideCursor(Qt.CursorShape.CrossCursor)

    def paintEvent(self, event):
        if self.is_snipping and self.begin and self.end:
            painter = QPainter(self)
            painter.setPen(QPen(QColor(0, 122, 255), 2))
            painter.setBrush(QBrush(QColor(0, 0, 0, 0)))
            rect = QRect(self.begin, self.end)
            painter.drawRect(rect)

    def mousePressEvent(self, event):
        # Eğer ilk bırakma henüz gerçekleşmediyse, bu yeni bir basmadır
        self.first_click_released = True 
        
        self.begin = event.pos()
        self.end = event.pos()
        self.is_snipping = True
        self.update()

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        # Eğer bu, shake işleminden kalan "bırakma" olayı ise yoksay
        if not self.first_click_released:
            self.first_click_released = True
            return

        self.is_snipping = False
        
        # Koordinatları normalize et
        if not self.begin or not self.end:
            self.begin = None
            self.end = None
            self.update()
            return

        x1 = min(self.begin.x(), self.end.x())
        y1 = min(self.begin.y(), self.end.y())
        x2 = max(self.begin.x(), self.end.x())
        y2 = max(self.begin.y(), self.end.y())
        
        # Eğer seçim çok küçükse KAPATMA, sadece seçimi sıfırla
        if x2 - x1 < 10 or y2 - y1 < 10: 
            self.begin = None
            self.end = None
            self.update()
            return

        # Geçerli bir seçim yapıldı -> Görüntüyü al ve kapat
        self.close() # closeEvent override'ı çağırır, orada cursor restore edilir
        self.hide()
        QApplication.processEvents()
        
        # Tüm ekranlardan grab (Sanal Masaüstü koordinatları)
        # grabWindow fonksiyonu (0, x, y, w, h) parametreleri ile global koordinatları kullanır
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(0, x1, y1, x2 - x1, y2 - y1)
        
        byte_array = QBuffer()
        byte_array.open(QIODevice.OpenModeFlag.ReadWrite)
        screenshot.save(byte_array, "PNG")
        
        # Sinyali gönder
        self.snippet_taken.emit(byte_array.data().data())

    def closeEvent(self, event):
        # Override cursor'ı kaldır
        while QApplication.overrideCursor() is not None:
            QApplication.restoreOverrideCursor()
        event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
