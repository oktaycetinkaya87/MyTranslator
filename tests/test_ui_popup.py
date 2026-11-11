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

def show_translation(popup, source="Src", translation="Trans"):
    """Bir çevirinin bittiği durumu, akışın gönderdiği iletilerle kurar."""
    popup.update_content(None)
    popup.update_content({"source_text": source})
    popup.update_content({"chunk": translation})
    popup.update_content({"finished": True})

def test_refine_signal(popup, qtbot):
    show_translation(popup)
    assert popup.refine_btn.isVisible()

    with qtbot.waitSignal(popup.refine_requested, timeout=1000) as blocker:
        qtbot.mouseClick(popup.refine_btn, Qt.MouseButton.LeftButton)

    # Kaynak olarak ilk çeviri değil, çevirinin yapıldığı özgün metin gider
    assert blocker.args == ["Src", "Trans"]

    # Yanıt gelene kadar düğmeler gizli, ilerleme çubuğu açık
    assert not popup.refine_btn.isVisible()
    assert not popup.copy_btn.isVisible()
    assert popup.progress_bar.isVisible()

def test_refine_replaces_translation(popup):
    show_translation(popup)
    popup.on_refine_click()

    popup.update_content({"clear_translation": True})
    popup.update_content({"chunk": "Refined"})
    popup.update_content({"finished": True})

    assert popup.translated_text.toPlainText() == "Refined"
    assert popup.refine_btn.isVisible()
    assert not popup.progress_bar.isVisible()
    assert popup.info_label.text() == ""

def test_refine_ignores_click_while_running(popup, qtbot):
    show_translation(popup)
    popup.on_refine_click()
    popup.update_content({"clear_translation": True})
    popup.update_content({"chunk": "Half"})

    # Yarım gelen metin ikinci bir istek olarak gönderilmez
    with qtbot.assertNotEmitted(popup.refine_requested):
        popup.on_refine_click()

@pytest.mark.parametrize("failed_stream", [
    [{"chunk": " [Error: 429 RESOURCE_EXHAUSTED]"}, {"finished": True}],  # API hatası
    [{"chunk": "Half "}, {"chunk": " [Error: reset]"}, {"finished": True}],  # akış ortasında hata
    [{"finished": True}],  # model boş döndü
    ["Error: thread failed"],  # işleyici hatası
])
def test_failed_refine_restores_translation(popup, qtbot, failed_stream):
    show_translation(popup)
    popup.on_refine_click()
    popup.update_content({"clear_translation": True})
    for message in failed_stream:
        popup.update_content(message)

    assert popup.translated_text.toPlainText() == "Trans"
    assert popup.info_label.text().startswith("⚠️")
    assert popup.refine_btn.isVisible()

    # Yeniden deneme hata iletisini değil, çeviriyi gönderir
    with qtbot.waitSignal(popup.refine_requested, timeout=1000) as blocker:
        popup.on_refine_click()
    assert blocker.args == ["Src", "Trans"]

def test_refine_signal_skips_placeholder_source(popup, qtbot):
    # Ekran çevirisinde model kaynak metni ayırmadıysa kutuda yer tutucu kalır
    show_translation(popup, source="[Görsel İşleniyor...]")

    with qtbot.waitSignal(popup.refine_requested, timeout=1000) as blocker:
        popup.on_refine_click()

    assert blocker.args == ["", "Trans"]

def test_refine_sends_source_with_markup_unchanged(popup, qtbot):
    # Etiketle başlayan metni Qt zengin metin sanıp etiketleri yutabilir
    source = "<b>Results</b> were significant (p < .05)."
    show_translation(popup, source=source)

    with qtbot.waitSignal(popup.refine_requested, timeout=1000) as blocker:
        popup.on_refine_click()

    assert blocker.args == [source, "Trans"]

@pytest.mark.parametrize("not_a_translation", [
    "",
    " [Hata: 503 UNAVAILABLE]",
    "Half a sentence [Error: reset]",
    "❌ Çeviri limitine ulaştınız! (0/100 kaldı)",
])
def test_refine_needs_a_translation(popup, qtbot, not_a_translation):
    popup.update_content({"source_text": "Src"})
    popup.update_text(not_a_translation)

    with qtbot.assertNotEmitted(popup.refine_requested):
        popup.on_refine_click()

    assert popup.translated_text.toPlainText() == not_a_translation
