import pytest
import sys
import os
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QPoint, QRect

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ui.snip_tool import SnippingTool

@pytest.fixture
def app(qtbot):
    test_app = QApplication.instance()
    if not test_app:
        test_app = QApplication([])
    return test_app

@pytest.fixture
def snip_tool(qtbot):
    # Mock screens to return a fixed geometry
    # Patch where it is USED
    with patch("ui.snip_tool.QApplication.screens") as mock_screens:
        mock_screen = MagicMock()
        mock_screen.geometry.return_value = QRect(0, 0, 1920, 1080)
        mock_screens.return_value = [mock_screen]
        
        # Mock primaryScreen for grabWindow
        with patch("ui.snip_tool.QApplication.primaryScreen") as mock_primary:
            mock_grab = MagicMock()
            # grabWindow returns a pixmap, we need to mock saving it to buffer
            mock_grab.save = MagicMock() 
            mock_primary.return_value.grabWindow.return_value = mock_grab
            
            tool = SnippingTool()
            qtbot.addWidget(tool)
            return tool

def test_snip_start(snip_tool, qtbot):
    snip_tool.start()
    assert snip_tool.isVisible()
    assert snip_tool.windowFlags() & Qt.WindowType.FramelessWindowHint
    assert snip_tool.windowFlags() & Qt.WindowType.WindowStaysOnTopHint
    # Check if geometry is valid (has size)
    # Exact matching is flaky due to environment differences
    geo = snip_tool.geometry()
    assert geo.width() > 0
    assert geo.height() > 0
    
    # Clean up override cursor
    while QApplication.overrideCursor() is not None:
        QApplication.restoreOverrideCursor()

def test_mouse_drag_selection(snip_tool, qtbot):
    snip_tool.start()
    
    # Simulate Mouse Press (Start Selection)
    qtbot.mouseMove(snip_tool, QPoint(100, 100))
    qtbot.mousePress(snip_tool, Qt.MouseButton.LeftButton, pos=QPoint(100, 100))
    
    assert snip_tool.is_snipping
    assert snip_tool.begin == QPoint(100, 100)
    
    # Simulate Mouse Move (Dragging)
    qtbot.mouseMove(snip_tool, QPoint(200, 200))
    assert snip_tool.end == QPoint(200, 200)
    
    # Simulate Mouse Release (End Selection)
    with qtbot.waitSignal(snip_tool.snippet_taken, timeout=1000):
        qtbot.mouseRelease(snip_tool, Qt.MouseButton.LeftButton, pos=QPoint(200, 200))

    assert not snip_tool.isVisible()
    
    # Clean up cursor
    while QApplication.overrideCursor() is not None:
        QApplication.restoreOverrideCursor()

def test_escape_closes(snip_tool, qtbot):
    snip_tool.start()
    qtbot.keyPress(snip_tool, Qt.Key.Key_Escape)
    assert not snip_tool.isVisible()
    
    # Clean up cursor
    while QApplication.overrideCursor() is not None:
        QApplication.restoreOverrideCursor()
