import pytest
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from unittest.mock import patch
from ui.popup_window import TranslationPopup

# Ensure QApplication exists (pytest-qt handles this too, but for safety)
@pytest.fixture
def app(qtbot):
    test_app = QApplication.instance()
    if not test_app:
        test_app = QApplication([])
    return test_app

@pytest.fixture
def popup(qtbot):
    window = TranslationPopup()
    qtbot.addWidget(window)
    window.show() # Force show for visibility tests
    return window

def test_popup_initial_state(popup):
    assert popup.windowTitle() == "MyTranslator"
    assert popup.width() == 500
    assert popup.height() == 480
    assert not popup.copy_btn.isVisible()
    assert not popup.humanize_btn.isVisible()
    assert not popup.progress_bar.isVisible()

def test_start_loading(popup):
    popup.start_loading()
    assert popup.progress_bar.isVisible()
    assert popup.original_text.toPlainText() == "Veri alınıyor..."
    assert popup.translated_text.toPlainText() == ""
    assert not popup.copy_btn.isVisible()

def test_update_content_text(popup):
    popup.update_content({"source_text": "Merhaba", "translation": "Hello", "finished": True})
    assert popup.original_text.toPlainText() == "Merhaba"
    assert popup.translated_text.toPlainText() == "Hello"
    assert not popup.progress_bar.isVisible()
    # Check enabled state instead of isVisible if window is hidden
    assert popup.copy_btn.isEnabled()

def test_buttons_click(popup, qtbot):
    popup.update_content({"translation": "Test Translation", "finished": True})
    
    # Mock QTimer to prevent crash after test
    with patch("PyQt6.QtCore.QTimer.singleShot"):
         qtbot.mouseClick(popup.copy_btn, Qt.MouseButton.LeftButton)
         assert popup.windowTitle() == "✅ Kopyalandı!"

    with qtbot.waitSignal(popup.settings_requested, timeout=1000):
        qtbot.mouseClick(popup.settings_btn, Qt.MouseButton.LeftButton)

def test_humanize_signal(popup, qtbot):
    popup.update_content({"source_text": "Src", "translation": "Trans", "finished": True})
    
    with qtbot.waitSignal(popup.humanize_requested, timeout=1000) as blocker:
        qtbot.mouseClick(popup.humanize_btn, Qt.MouseButton.LeftButton)
    
    # Check signal arguments. 
    # Logic in popup: source_ref = self.original_translation if self.original_translation else current_text
    # original_translation is set when finished=True.
    # So if we passed "translation": "Trans", original_translation becomes "Trans"
    # Wait, original_translation is set to translated_text.toPlainText() when finished.
    # So source_ref = "Trans". args = ["Trans", "Trans"]
    assert blocker.args == ["Trans", "Trans"]
