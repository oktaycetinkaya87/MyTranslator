import pytest
import sys
import os
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication, QSlider, QLabel
from PyQt6.QtCore import Qt

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ui.settings_window import SettingsWindow

# Ensure QApplication exists
@pytest.fixture
def app(qtbot):
    test_app = QApplication.instance()
    if not test_app:
        test_app = QApplication([])
    return test_app

@pytest.fixture
def settings_window(qtbot):
    # Mock DatabaseManager
    with patch("ui.settings_window.DatabaseManager") as MockDB:
        mock_db = MockDB.return_value
        mock_db.get_setting.return_value = 5  # Default sensitivity
        
        # Mock ClipboardHandler
        mock_clipboard = MagicMock()
        mock_clipboard.usage_tracker = MagicMock()
        mock_clipboard.usage_tracker.limit = 100
        mock_clipboard.usage_tracker.get_remaining.return_value = 50 # Default to limited
        
        window = SettingsWindow(clipboard_handler=mock_clipboard)
        qtbot.addWidget(window)
        window.show()
        return window

def test_settings_init(settings_window):
    assert settings_window.windowTitle() == "Ayarlar"
    assert settings_window.slider.value() == 5
    assert settings_window.val_label.text() == "5"

def test_slider_change(settings_window, qtbot):
    # Set slider to 8
    settings_window.slider.setValue(8)
    
    assert settings_window.val_label.text() == "8"
    # Verify DB update
    settings_window.db_manager.set_setting.assert_called_with("shake_sensitivity", 8)
    # Verify clipboard handler update
    settings_window.clipboard_handler.set_sensitivity.assert_called_with(8)

def test_usage_display_limited(settings_window):
    # Setup limited usage
    settings_window.clipboard_handler.usage_tracker.get_remaining.return_value = 50
    
    # Re-init settings to refresh UI
    settings_window.init_general_settings()
    
    # Check for specific text or labels
    # We look for "Kalan Hakkınız"
    labels = settings_window.findChildren(QLabel)
    assert any("Kalan Hakkınız" in l.text() for l in labels)
    assert any("50 / 100" in l.text() for l in labels)

def test_usage_display_unlimited(settings_window):
    # Setup unlimited usage
    settings_window.clipboard_handler.usage_tracker.get_remaining.return_value = -1
    
    # Re-init settings to refresh UI
    # Note: init_general_settings appends to layout, might be messy but verifiable
    # Better to create a new window or just call the method and check new widgets
    
    # Let's create a fresh window for this test to avoid layout duplication
    with patch("ui.settings_window.DatabaseManager"):
        mock_cb = MagicMock()
        mock_cb.usage_tracker.get_remaining.return_value = -1
        win = SettingsWindow(clipboard_handler=mock_cb)
        
        labels = win.findChildren(QLabel)
        assert any("Limitsiz Erişim" in l.text() for l in labels)
