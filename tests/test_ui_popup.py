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
    assert not popup.refine_btn.isVisible()
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

def test_refine_signal(popup, qtbot):
    popup.update_content({"source_text": "Src", "translation": "Trans", "finished": True})

    with qtbot.waitSignal(popup.refine_requested, timeout=1000) as blocker:
        qtbot.mouseClick(popup.refine_btn, Qt.MouseButton.LeftButton)

    # Kaynak olarak ilk çeviri değil, çevirinin yapıldığı özgün metin gider
    assert blocker.args == ["Src", "Trans"]
    assert popup.translated_text.toPlainText() == "Üslup iyileştiriliyor..."

def test_refine_signal_skips_placeholder_source(popup, qtbot):
    # Ekran çevirisinde kaynak kutusunda yer tutucu kalmış olabilir
    popup.update_content({"source_text": "[Görsel İşleniyor...]", "translation": "Trans", "finished": True})

    with qtbot.waitSignal(popup.refine_requested, timeout=1000) as blocker:
        qtbot.mouseClick(popup.refine_btn, Qt.MouseButton.LeftButton)

    assert blocker.args == ["", "Trans"]

def test_refine_click_without_translation_does_nothing(popup, qtbot):
    popup.update_content({"source_text": "Src"})

    with qtbot.assertNotEmitted(popup.refine_requested):
        popup.on_refine_click()

    assert popup.translated_text.toPlainText() == ""
