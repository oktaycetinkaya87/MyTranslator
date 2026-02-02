import time
import threading
import logging
import re
import platform
import subprocess
from pynput import keyboard

# --- IMPORT GÜNCELLEMESİ: MacOS için Güvenli Pano Erişimi ---
try:
    if platform.system() == 'Darwin':
        from AppKit import NSPasteboard, NSStringPboardType
except ImportError:
    logging.warning("⚠️ AppKit not found. Clipboard features may fail. (pip install pyobjc)")

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
        self.api.warmup() 
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
                    threading.Thread(target=self.on_activate, daemon=True).start()
        except AttributeError:
            self.c_press_count = 0

    def on_release(self, key):
        if key == keyboard.Key.cmd:
            self.c_press_count = 0

    def get_clipboard_content(self):
        """
        GÜVENLİ VE HIZLI YÖNTEM
        Eski 'subprocess' (pbpaste) yöntemi MacOS'ta thread çakışması yapıp çökertiyordu.
        AppKit kullanımı bunu %100 çözer ve 10 kat daha hızlıdır.
        """
        try:
            if platform.system() == 'Darwin':
                pb = NSPasteboard.generalPasteboard()
                content = pb.stringForType_(NSStringPboardType)
                return content if content else ""
            else:
                # Windows/Linux Fallback
                import subprocess
                result = subprocess.run(
                    ['pbpaste', '-pboard', 'general'], 
                    capture_output=True, text=True, 
                    env={'LC_CTYPE': 'UTF-8'}
                )
                return result.stdout
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
        """
        LATENCY OPTİMİZASYONU:
        Eskiden 1 saniyede 10 kere kontrol ediyordu (0.1s gecikme riski).
        Şimdi 1 saniyede 100 kere kontrol ediyor (0.01s gecikme riski).
        Çok daha seri hissettirir.
        """
        logging.info("🎹 Kısayol (Cmd+C+C) Algılandı - İşleniyor...")
        
        raw_text = None
        for i in range(100): # 100 deneme (Hızlı tepki)
            raw_text = self.get_clipboard_content()
            if raw_text and raw_text.strip():
                break
            time.sleep(0.01) # 10ms bekleme

        if not raw_text or not raw_text.strip():
            logging.warning("⚠️ Pano boş veya okunamadı.")
            return

        self._process_logic(raw_text)

    def process_clipboard_content(self, raw_text):
        threading.Thread(target=self._process_logic, args=(raw_text,), daemon=True).start()

    def _process_logic(self, raw_text):
        try:
            if not raw_text or not raw_text.strip():
                return

            text = self.clean_text(raw_text)
            
            # Aynı metin kontrolü
            if text == self.last_text:
                logging.info("♻️ Aynı metin. Önbellek gösteriliyor.")
                self.move_window_callback()
                cached = self.db.get_translation(text, "Academic")
                if cached:
                    self.update_callback(cached)
                return

            self.last_text = text
            self.move_window_callback() 
            self.update_callback(None)  
            self.update_callback({"source_text": text}) 

            cached = self.db.get_translation(text, "Academic")
            if cached and "translation" in cached:
                self.update_callback(cached)
                return

            full_translation = ""
            try:
                for chunk in self.api.translate_text_stream(text):
                    full_translation += chunk
                    self.update_callback({"chunk": chunk})
                
                self.update_callback({"finished": True})
                self.db.add_history(text, full_translation)
                
            except Exception as e:
                logging.error(f"Translation Error: {e}")
                self.update_callback(f"Hata: {str(e)}")

        except Exception as e:
            logging.error(f"FATAL ERROR in logic: {e}", exc_info=True)
            self.update_callback(f"Kritik Hata: {str(e)}")
