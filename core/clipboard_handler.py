import time
import threading
from PyQt6.QtCore import QObject, pyqtSignal
from pynput import keyboard

class ClipboardListener(QObject):
    hotkey_triggered = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.listener = None
        self.last_c_press_time = 0
        self.c_press_count = 0
        self._running = False

    def start(self):
        if self._running: return
        self._running = True
        threading.Thread(target=self._run_listener, daemon=True).start()

    def stop(self):
        self._running = False
        if self.listener:
            self.listener.stop()

    def _run_listener(self):
        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as self.listener:
            self.listener.join()

    def on_press(self, key):
        if not self._running: return False
        try:
            if key == keyboard.Key.cmd:
                pass # Just CMD pressed
            elif hasattr(key, 'char') and key.char == 'c':
                current_time = time.time()
                # 0.5s threshold for double press
                if current_time - self.last_c_press_time < 0.5:
                    self.c_press_count += 1
                else:
                    self.c_press_count = 1
                
                self.last_c_press_time = current_time

                if self.c_press_count == 2:
                    self.c_press_count = 0
                    self.hotkey_triggered.emit()
        except AttributeError:
            self.c_press_count = 0

    def on_release(self, key):
        if key == keyboard.Key.cmd:
            self.c_press_count = 0
