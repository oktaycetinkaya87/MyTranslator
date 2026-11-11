import pytest
import sys
import os
import time
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# We need the real Enum for button comparison if possible, or we mock it if pynput is not present
try:
    from pynput import mouse
    LEFT_BUTTON = mouse.Button.left
except ImportError:
    # Fallback if not installed (though it should be)
    LEFT_BUTTON = MagicMock()

# Mock listener classes to avoid side effects
with patch("pynput.mouse.Listener"), patch("pynput.keyboard.Listener"):
    from core.clipboard_handler import ClipboardHandler

@pytest.fixture
def clipboard_handler():
    # Mock callbacks
    mock_update = MagicMock()
    mock_move = MagicMock()
    mock_snip = MagicMock()
    
    # Mock external services
    with patch("core.clipboard_handler.APIService") as MockAPI, \
         patch("core.clipboard_handler.DatabaseManager") as MockDB, \
         patch("core.clipboard_handler.UsageTracker") as MockTracker:
        
        # Configure DB Mock BEFORE instantiation so __init__ sees it
        MockDB.return_value.get_setting.return_value = "5"
        
        handler = ClipboardHandler(mock_update, mock_move, mock_snip)
        handler.api = MockAPI.return_value
        handler.db = MockDB.return_value
        handler.usage_tracker = MockTracker.return_value
        
        # Default behavior: Limit not reached usage
        handler.usage_tracker.check_limit_reached.return_value = False
        handler.usage_tracker.current_usage = 0
        
        return handler

def test_usage_limit_reached(clipboard_handler):
    # Setup limit reached
    clipboard_handler.usage_tracker.check_limit_reached.return_value = True
    clipboard_handler.usage_tracker.limit = 10
    
    # Try to process text
    clipboard_handler._process_text_logic("Test Text")
    
    # Should call update_callback with error message about limit
    clipboard_handler.update_callback.assert_called_with("❌ Çeviri limitine ulaştınız! (0/10 kaldı)")
    
    # Should NOT call API
    clipboard_handler.api.translate_text_stream.assert_not_called()

def test_shake_logic_trigger(clipboard_handler):
    # Simulate Shake Logic (Click + Shake)
    # 1. Mouse Press
    clipboard_handler.on_click(0, 0, LEFT_BUTTON, True) 
    assert clipboard_handler.left_mouse_pressed
    
    # 2. Prime the shake logic (Reset time, init last_x)
    import time
    clipboard_handler.shake_reset_time = time.time()
    clipboard_handler.last_x = 0
    
    # 3. Simulate rapid movement (shake)
    # Default sensitivity 5 -> dist 90px
    dist = 100
    
    # Move Right (accumulate)
    clipboard_handler.on_move(dist, 0)
    
    # Move Left (Direction Change 1)
    clipboard_handler.on_move(0, 0) 
    
    # Move Right (Direction Change 2)
    clipboard_handler.on_move(dist, 0)
    
    # Move Left (Direction Change 3 -> Trigger! Required shakes is 3 for sens 5)
    clipboard_handler.on_move(0, 0)
    
    # Verify Snip Triggered
    clipboard_handler.trigger_snip_callback.assert_called_once()

def test_process_text_cached(clipboard_handler):
    # Setup cache hit
    clipboard_handler.db.get_translation.return_value = "Cached Translation"
    
    clipboard_handler._process_text_logic("Hello")
    
    # Should update UI with cached value
    clipboard_handler.update_callback.assert_any_call("Cached Translation")
    # API should not be called
    clipboard_handler.api.translate_text_stream.assert_not_called()
    # Usage should increment
    clipboard_handler.usage_tracker.increment.assert_called_once()

def test_process_text_api(clipboard_handler):
    # Setup cache miss
    clipboard_handler.db.get_translation.return_value = None
    clipboard_handler.api.translate_text_stream.return_value = ["Hel", "lo"]
    
    clipboard_handler._process_text_logic("Hello")
    
    # Should stream chunks
    clipboard_handler.update_callback.assert_any_call({"chunk": "Hel"})
    clipboard_handler.update_callback.assert_any_call({"chunk": "lo"})
    clipboard_handler.update_callback.assert_any_call({"finished": True})
    
    # Should save to DB
    clipboard_handler.db.add_history.assert_called_with("Hello", "Hello")
    # Usage increment
    clipboard_handler.usage_tracker.increment.assert_called_once()

def test_refine_logic_streams_into_popup(clipboard_handler):
    clipboard_handler.api.refine_text_stream.return_value = iter(["Refined ", "text"])

    clipboard_handler._refine_logic("Source", "Current")

    clipboard_handler.api.refine_text_stream.assert_called_once_with("Source", "Current")
    assert [c.args[0] for c in clipboard_handler.update_callback.call_args_list] == [
        {"clear_translation": True},
        {"chunk": "Refined "},
        {"chunk": "text"},
        {"finished": True},
    ]

def test_refine_logic_reports_failure_as_error(clipboard_handler):
    clipboard_handler.api.refine_text_stream.side_effect = RuntimeError("boom")

    clipboard_handler._refine_logic("Source", "Current")

    # "Error:" ile başlayan ileti pencerede çeviri kutusuna değil hata satırına yazılır
    clipboard_handler.update_callback.assert_called_with("Error: boom")
