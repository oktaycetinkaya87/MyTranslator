from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QRect, pyqtSignal, QBuffer, QIODevice
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath

class SnippingTool(QWidget):
    snippet_taken = pyqtSignal(object) 

    def __init__(self):
        super().__init__()
        # MacOS için Tool yerine Window kullanmak bazen daha stabildir
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True) # Fare hareketini sürekli izle
        
        # --- GÖRSEL AYARLAR ---
        # Karartma Rengi (Siyahın %60'ı)
        self.overlay_color = QColor(0, 0, 0, 160) 
        # Seçim Çerçevesi Rengi (Mavi)
        self.border_color = QColor(65, 155, 255)
        
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
        """Spotlight Efekti (Delik Açma) ile Çizim"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        path = QPainterPath()
        path.setFillRule(Qt.FillRule.OddEvenFill) # Kesişim kuralı
        
        # 1. Katman: Tüm Ekran
        path.addRect(self.rect().toRectF())

        # Eğer seçim yapılıyorsa 'Delik' aç
        if self.is_snipping and self.begin and self.end:
            # Koordinatları normalize et
            x1 = min(self.begin.x(), self.end.x())
            y1 = min(self.begin.y(), self.end.y())
            x2 = max(self.begin.x(), self.end.x())
            y2 = max(self.begin.y(), self.end.y())
            selection_rect = QRect(x1, y1, x2 - x1, y2 - y1)
            
            # 2. Katman: Seçilen Alan (Delik)
            path.addRect(selection_rect.toRectF())
            
            # Boyama (Delik hariç her yer boyanır)
            painter.setBrush(self.overlay_color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPath(path)
            
            # Seçim alanının etrafına mavi çerçeve çiz
            painter.setPen(QPen(self.border_color, 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(selection_rect)
            
            # Boyutları yaz
            text = f"{selection_rect.width()} x {selection_rect.height()}"
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(selection_rect.topLeft().x(), selection_rect.topLeft().y() - 10, text)
            
        else:
            # Henüz seçim yok, her yeri karart
            painter.fillRect(self.rect(), self.overlay_color)

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
