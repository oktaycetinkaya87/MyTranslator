import time
import threading
import logging
import re
from pynput import keyboard

# Mac-Specific Clipboard Access
try:
    from AppKit import NSPasteboard, NSStringPboardType
except ImportError:
    logging.warning("⚠️ AppKit not found. Clipboard features may fail.")

from core.api_service import APIService
from database.db_manager import DatabaseManager

# --- COMPILED REGEX ---
RE_HYPHEN = re.compile(r'-\s*\n\s*')
RE_NEWLINES = re.compile(r'[\n\r]+')
RE_SPACES = re.compile(r'\s+')

class ClipboardHandler:
    def __init__(self, update_callback, move_window_callback):
        self.update_callback = update_callback
        self.move_window_callback = move_window_callback
        
        # Services
        self.api = APIService()
        self.api.warmup() # Warmup on init
        self.db = DatabaseManager()
        
        # State
        self.last_text = ""
        self.last_c_press_time = 0
        self.c_press_count = 0
        self._running = False
        self.listener = None

    def start(self):
        if self._running: return
        self._running = True
        threading.Thread(target=self._run_listener, daemon=True).start()
        logging.info("🎧 Clipboard Handler Started (Cmd+C+C Listening...)")

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
                pass 
            elif hasattr(key, 'char') and key.char == 'c':
                current_time = time.time()
                if current_time - self.last_c_press_time < 0.5:
                    self.c_press_count += 1
                else:
                    self.c_press_count = 1
                
                self.last_c_press_time = current_time

                if self.c_press_count == 2:
                    self.c_press_count = 0
                    # Run logic in a separate thread to avoid blocking Listener
                    threading.Thread(target=self.on_activate, daemon=True).start()
        except AttributeError:
            self.c_press_count = 0

    def on_release(self, key):
        if key == keyboard.Key.cmd:
            self.c_press_count = 0

    def get_clipboard_content(self):
        """Thread-safe clipboard read using AppKit (macOS)"""
        try:
            pb = NSPasteboard.generalPasteboard()
            content = pb.stringForType_(NSStringPboardType)
            return content
        except Exception as e:
            logging.error(f"Clipboard Read Error: {e}")
            return None

    def clean_text(self, text):
        if not text: return ""
        text = RE_HYPHEN.sub('', text)
        text = RE_NEWLINES.sub(' ', text)
        text = RE_SPACES.sub(' ', text)
        return text.strip()

    def on_activate(self):
        logging.info("🎹 Kısayol (Cmd+C+C) Algılandı")
        
        # 1. Pano Verisini Al (Retry Logic)
        raw_text = None
        for i in range(10): # 1.0s wait
            raw_text = self.get_clipboard_content()
            if raw_text and raw_text.strip():
                break
            time.sleep(0.1)
        
        if not raw_text or not raw_text.strip():
            logging.warning("⚠️ Pano boş, işlem iptal.")
            return

        # 2. Temizle
        text = self.clean_text(raw_text)
        
        # 3. Aynı metin kontrolü
        if text == self.last_text:
            logging.info("♻️ Aynı metin. Önbellek gösteriliyor.")
            self.move_window_callback() # Show window
            
            cached = self.db.get_translation(text, "Academic")
            if cached:
                self.update_callback(cached)
            return

        # 4. Yeni İşlem -> UI Başlat
        self.last_text = text
        self.move_window_callback() # Teleport & Show
        self.update_callback(None)  # Start Loading
        self.update_callback({"source_text": text}) # Show Source

        # 5. DB Kontrol
        cached = self.db.get_translation(text, "Academic")
        if cached and "translation" in cached:
            self.update_callback(cached)
            return

        # 6. API İsteği (Streaming)
        full_translation = ""
        try:
            for chunk in self.api.translate_text_stream(text):
                full_translation += chunk
                # Send CHUNK for smooth appending (don't scroll user)
                self.update_callback({"chunk": chunk})
            
            # Send Finished Signal (Hides Progress Bar)
            self.update_callback({"finished": True})
            
            # Save to History
            self.db.add_history(text, full_translation)
            
        except Exception as e:
            logging.error(f"Translation Error: {e}")
            self.update_callback(f"Hata: {str(e)}")
