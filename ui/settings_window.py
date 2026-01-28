from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
    QPushButton, QLineEdit, QLabel, QHeaderView, QTabWidget, QMessageBox, QAbstractItemView
)
from PyQt6.QtCore import Qt
from database.db_manager import DatabaseManager

class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager() # Uses the Singleton instance
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("Ayarlar & Geçmiş")
        self.resize(700, 500)
        
        layout = QVBoxLayout()
        self.tabs = QTabWidget()
        
        # TAB 1: Translation History
        self.history_tab = QWidget()
        self.init_history_tab()
        self.tabs.addTab(self.history_tab, "Çeviri Geçmişi")
        
        # TAB 2: Custom Dictionary
        self.dict_tab = QWidget()
        self.init_dict_tab()
        self.tabs.addTab(self.dict_tab, "Sözlüğüm")
        
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def init_history_tab(self):
        layout = QVBoxLayout()
        
        # History Table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(3)
        self.history_table.setHorizontalHeaderLabels(["Tarih", "Kaynak Metin", "Çeviri"])
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        refresh_btn = QPushButton("Yenile")
        refresh_btn.clicked.connect(self.load_history)
        
        layout.addWidget(self.history_table)
        layout.addWidget(refresh_btn)
        self.history_tab.setLayout(layout)

    def init_dict_tab(self):
        layout = QVBoxLayout()
        
        # Input Area
        input_layout = QHBoxLayout()
        self.term_input = QLineEdit()
        self.term_input.setPlaceholderText("Terim (örn. Anxiety)")
        
        self.def_input = QLineEdit()
        self.def_input.setPlaceholderText("Tanım / Karşılık (örn. Kaygı)")
        
        add_btn = QPushButton("Ekle")
        add_btn.setStyleSheet("background-color: #28a745; color: white; font-weight: bold;")
        add_btn.clicked.connect(self.add_term)
        
        input_layout.addWidget(self.term_input)
        input_layout.addWidget(self.def_input)
        input_layout.addWidget(add_btn)
        
        # Dictionary Table
        self.dict_table = QTableWidget()
        self.dict_table.setColumnCount(3)
        self.dict_table.setHorizontalHeaderLabels(["Terim", "Tanım", "İşlem"])
        self.dict_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        layout.addLayout(input_layout)
        layout.addWidget(self.dict_table)
        self.dict_tab.setLayout(layout)

    def showEvent(self, event):
        # Load data when window is shown
        self.load_history()
        self.load_dictionary()
        super().showEvent(event)

    def load_history(self):
        # Fetch last 50 items (Safe Loading)
        history = self.db_manager.get_history(limit=50)
        self.history_table.setRowCount(len(history))
        
        for i, row in enumerate(history):
            self.history_table.setItem(i, 0, QTableWidgetItem(str(row['timestamp'])[:16]))
            self.history_table.setItem(i, 1, QTableWidgetItem(row['original_text']))
            self.history_table.setItem(i, 2, QTableWidgetItem(row['translated_text']))

    def load_dictionary(self):
        terms = self.db_manager.get_all_terms()
        self.dict_table.setRowCount(len(terms))
        
        for i, row in enumerate(terms):
            self.dict_table.setItem(i, 0, QTableWidgetItem(row['term']))
            self.dict_table.setItem(i, 1, QTableWidgetItem(row['definition']))
            
            # Delete Button per row
            del_btn = QPushButton("Sil")
            del_btn.setStyleSheet("color: red;")
            del_btn.clicked.connect(lambda _, r=row['id']: self.delete_term(r))
            self.dict_table.setCellWidget(i, 2, del_btn)

    def add_term(self):
        term = self.term_input.text().strip()
        definition = self.def_input.text().strip()
        
        # SECURITY: Input Validation
        if not term or not definition:
            QMessageBox.warning(self, "Hata", "Terim ve Tanım alanları boş olamaz.")
            return
            
        if len(term) > 100 or len(definition) > 200:
            QMessageBox.warning(self, "Hata", "Girdi çok uzun! Lütfen kısaltın.")
            return

        success = self.db_manager.add_term(term, definition)
        if success:
            self.term_input.clear()
            self.def_input.clear()
            self.load_dictionary()
            QMessageBox.information(self, "Başarılı", "Terim eklendi.")
        else:
            QMessageBox.critical(self, "Hata", "Terim eklenemedi (Zaten var olabilir).")

    def delete_term(self, term_id):
        confirm = QMessageBox.question(
            self, "Onay", "Bu terimi silmek istediğine emin misin?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.db_manager.delete_term(term_id)
            self.load_dictionary()
