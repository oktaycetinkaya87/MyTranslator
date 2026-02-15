import pytest
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication, QPushButton, QLabel
from PyQt6.QtCore import Qt
from ui.history_window import HistoryWindow

# Ensure QApplication exists (pytest-qt handles this too, but for safety)
@pytest.fixture
def app(qtbot):
    test_app = QApplication.instance()
    if not test_app:
        test_app = QApplication([])
    return test_app

@pytest.fixture
def history(qtbot):
    with patch("ui.history_window.DatabaseManager") as MockDB:
        mock_db_instance = MockDB.return_value
        
        # Mock get_last_history for load_data
        mock_row = {"id": 1, "original_text": "S1", "translation": "T1", "timestamp": "2023-01-01"}
        mock_db_instance.get_last_history.return_value = [mock_row]

        window = HistoryWindow()
        qtbot.addWidget(window)
        return window

def test_history_window_title(history):
    assert history.windowTitle() == "Çeviri Geçmişi (Son 100)"

def test_load_data(history, qtbot):
    history.load_data()
    
    # Wait for the async loader (QTimer singleShot)
    def check_items():
        assert history.container_layout.count() >= 1
        
    qtbot.waitUntil(check_items, timeout=2000)
    
    # Get the widget
    item_widget = history.container_layout.itemAt(0).widget()
    # It's a custom widget, find labels inside
    labels = item_widget.findChildren(QLabel)
    # One label should have "S1"
    assert any("S1" in l.text() for l in labels)

def test_clear_history_click(history, qtbot):
    # Mock clear_history method on DB
    history.db.clear_history = MagicMock()
    
    # Find the Clear Button (it has text "Tümünü Temizle")
    clear_btn = None
    for btn in history.findChildren(QPushButton):
        if "Tümünü Temizle" in btn.text():
            clear_btn = btn
            break
            
    assert clear_btn is not None
    
    # We need to mock QMessageBox because it blocks the UI
    with patch("PyQt6.QtWidgets.QMessageBox.question") as mock_msg:
        from PyQt6.QtWidgets import QMessageBox
        mock_msg.return_value = QMessageBox.StandardButton.Yes
        
        # When clear is clicked, get_last_history should return empty list next time
        history.db.get_last_history.return_value = []
        
        qtbot.mouseClick(clear_btn, Qt.MouseButton.LeftButton)
        
        history.db.clear_history.assert_called_once()
        # Verify items cleared
        assert history.container_layout.count() == 0
