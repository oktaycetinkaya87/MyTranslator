from PyQt6.QtWidgets import (
    QMainWindow, QTextEdit, QVBoxLayout, QWidget, QLabel, 
    QSplitter, QProgressBar, QApplication, QPushButton, QHBoxLayout, QFrame
)
from PyQt6.QtCore import Qt, QTimer, QSize, QEvent, pyqtSignal
from PyQt6.QtGui import QCursor, QTextCursor, QIcon, QFont, QAction, QPixmap
import platform
import os
import subprocess
import re
try:
    if platform.system() == 'Darwin':
        from AppKit import NSApplication
except ImportError:
    pass

from ui.snip_tool import SnippingTool

# Kaynak kutusunda gösterilen ama gerçek kaynak metin olmayan yer tutucular
SOURCE_PLACEHOLDERS = ("Veri alınıyor...", "[Görsel İşleniyor...]")

class TranslationPopup(QMainWindow):
    # Doğal Yazım isteği: (kaynak metin, penceredeki çeviri) gönderir
    refine_requested = pyqtSignal(str, str)
    settings_requested = pyqtSignal()
    image_captured = pyqtSignal(bytes) # Yeni Sinyal 

    def __init__(self):
        super().__init__()

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
        
        # 1. LOGO (BÜYÜK) - HIGH DPI DESTEKLİ
        # logobuyuk.png dosyasını kullan, yoksa eskisine düş
        logo_path = os.path.join(os.getcwd(), "assets", "logobuyuk.png")
        if not os.path.exists(logo_path):
            logo_path = os.path.join(os.getcwd(), "assets", "app_icon.png")

        if os.path.exists(logo_path):
            self.logo_label = QLabel()
            
            # ⭐ HIGH DPI DESTEĞI
            dpr = QApplication.instance().devicePixelRatio()  # Ekran çözünürlük oranı (Retina için 2.0)
            target_height = 50
            
            # Yüksek çözünürlük için daha büyük pixmap yükle
            pixmap = QPixmap(logo_path)
            
            # Ölçeklendirmeyi DPR ile yap
            scaled_pixmap = pixmap.scaledToHeight(
                int(target_height * dpr),  # Retina için 2x boyut
                Qt.TransformationMode.SmoothTransformation
            )
            
            # DPR'yi pixmap'e bildir (bu kritik!)
            scaled_pixmap.setDevicePixelRatio(dpr)
            
            self.logo_label.setPixmap(scaled_pixmap)
            self.logo_label.setFixedHeight(target_height)
            
            # Sol boşlukları sıfırla ki sola yaslansın
            self.logo_label.setStyleSheet("padding: 0px; margin: 0px; border: none;")
            top_header_layout.addWidget(self.logo_label)
            
        # 2. BAŞLIK (KALDIRILDI)
        # self.title_label = QLabel("MyTranslator") ...
        
        top_header_layout.addStretch()
        
        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setFixedSize(30, 30)
        self.settings_btn.setToolTip("Ayarlar")
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; 
                border-radius: 15px;
                font-size: 16px;
                color: #555;
            }
            QPushButton:hover { background-color: #e0e0e0; }
        """)
        self.settings_btn.clicked.connect(self.settings_requested.emit)
        top_header_layout.addWidget(self.settings_btn)

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
        self.splitter.setHandleWidth(12) # İkon için yeterli alan
        
        # Splitter Handle Stili (İkonlu - Geri Döndü)
        self.splitter.setStyleSheet("""
            QSplitter::handle { 
                background-color: transparent; 
                image: url(assets/splitter_handle.png);
                image-position: center;
                background-repeat: no-repeat;
            }
        """)

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
            QTextEdit { 
                border: none; 
                border-bottom: 1px solid #E0E0E0; 
                color: #444; 
                font-size: 13px; 
                background-color: #FCFCFA; /* Warm White */
                padding: 10px; 
            }
        """ + scrollbar_style)
        
        # 2. ALT BÖLME (Konteyner)
        bottom_container = QWidget()
        bottom_container.setStyleSheet("background-color: #FFFFFF;") 
        
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
            QPushButton:hover { 
                background-color: #E3F2FD; /* Light Blue */
                border: 1px solid #BBDEFB;
            }
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

        # DOĞAL YAZIM BUTONU
        self.refine_btn = QPushButton("✨") 
        self.refine_btn.setToolTip("Doğal Yazım (üslubu iyileştir)")
        self.refine_btn.setFixedSize(32, 32)
        self.refine_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refine_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; 
                border: none;
                border-radius: 4px;
                font-size: 18px;
                color: #555;
            }
            QPushButton:hover { 
                background-color: #FFF8E1; /* Light Gold */
                color: #D4AF37; /* Metallic Gold */
                border: 1px solid #FFE082;
            }
        """)
        self.refine_btn.clicked.connect(self.on_refine_click)
        self.refine_btn.hide() # Başlangıçta gizli

        header_row_layout.addWidget(self.refine_btn)
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

        self.copy_btn.hide()
        self.refine_btn.hide()

    def stop_loading(self):
        self.progress_bar.hide()
        if self.translated_text.toPlainText():
            self.copy_btn.show()
            self.refine_btn.show()

    def update_content(self, data):
        try:
            if data is None:
                self.start_loading()
                # Eğer pencere gizliyse sadece görünür yap, TAŞIMA.
                # Taşıma işlemini 'move_signal' zaten yapıyor.
                if not self.isVisible():
                    self.show()
                return
                
            if isinstance(data, dict):
                if "clear_translation" in data and data["clear_translation"]:
                    self.translated_text.clear()

                if "source_text" in data:
                    raw_text = data["source_text"]
                    # Tek satır sonlarını boşlukla değiştir (Paragraf koru)
                    cleaned_text = re.sub(r'(?<!\n)\n(?!\n)', ' ', raw_text)
                    self.original_text.setText(cleaned_text)
                    self.adjust_input_height()
                if "chunk" in data:
                    self.append_chunk(data["chunk"])
                elif "translation" in data:
                    self.update_text(data["translation"])
                elif "finished" in data:
                    self.stop_loading()
                
            elif isinstance(data, str):
                self.stop_loading()
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

    def on_refine_click(self):
        """Doğal Yazım butonuna basılınca"""
        current_text = self.translated_text.toPlainText()
        if not current_text.strip():
            return

        # Anlam denetimi için çevirinin yapıldığı kaynak metin gönderilir
        source_text = self.original_text.toPlainText()
        if source_text in SOURCE_PLACEHOLDERS:
            source_text = ""

        self.translated_text.setPlainText("Üslup iyileştiriliyor...")
        self.refine_requested.emit(source_text, current_text)

    def adjust_input_height(self):
        doc_height = self.original_text.document().size().height()
        target_height = int(doc_height + 25) 
        total_height = self.splitter.height()
        max_allowed_height = total_height - 150
        final_height = max(60, min(target_height, max_allowed_height))
        self.splitter.setSizes([final_height, total_height - final_height])

    def start_snipping(self):
        # SnippingTool instance'ı yoksa oluştur
        if not hasattr(self, 'snip_tool'):
            self.snip_tool = SnippingTool()
            self.snip_tool.snippet_taken.connect(self.image_captured.emit)
        self.snip_tool.start()

    def show_at_cursor(self):
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
