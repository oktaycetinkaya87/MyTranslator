from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon
import sys
import os

app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)

tray = QSystemTrayIcon()
tray.setVisible(True)

# Generate simple icon
from PIL import Image, ImageDraw
img = Image.new('RGB', (64, 64), color = (255, 0, 0))
img.save('test_icon.png')

tray.setIcon(QIcon('test_icon.png'))

menu = QMenu()
action = menu.addAction("Exit")
action.triggered.connect(app.quit)
tray.setContextMenu(menu)

print("Tray started...")
app.exec()
