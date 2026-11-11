import time
import threading
import logging
import re
import platform
from pynput import keyboard, mouse 

# MacOS için Pano
try:
    if platform.system() == 'Darwin':
        from AppKit import NSPasteboard, NSStringPboardType
except ImportError:
    pass

from core.api_service import APIService
from database.db_manager import DatabaseManager
from core.usage_tracker import UsageTracker

RE_HYPHEN = re.compile(r'-\s*\n\s*')
RE_NEWLINES = re.compile(r'[\n\r]+')
RE_SPACES = re.compile(r'\s+')

from PyQt6.QtCore import QObject, pyqtSlot

class ClipboardHandler(QObject):
    def __init__(self, update_callback, move_window_callback, trigger_snip_callback):
        super().__init__()
        self.update_callback = update_callback
        self.move_window_callback = move_window_callback
        self.trigger_snip_callback = trigger_snip_callback 
        
        self.api = APIService()
        self.db = DatabaseManager()
        
        # ⭐ YENİ: Kullanım takipçisi
        self.usage_tracker = UsageTracker(limit=100)
        
        self._running = False
        
        # Klavye
        self.last_c_press_time = 0
        self.c_press_count = 0
        self.cmd_pressed = False
        
        # --- SHAKE AYARLARI ---
        self.left_mouse_pressed = False # 🖱️ Tetikleyici
        self.shake_count = 0
        self.last_x = 0
        self.accumulated_distance = 0
        self.current_direction = 0 
        self.shake_reset_time = 0
        
        # Kayıtlı hassasiyeti yükle
        try:
            saved = self.db.get_setting("shake_sensitivity", "5")
            self.set_sensitivity(int(saved))
        except:
            self.set_sensitivity(5)

    def set_sensitivity(self, level):
        """Level 1 (Zor) - Level 10 (Çok Hassas)"""
        self.sensitivity_level = level
        # Hassaslaştıkça mesafe kısalır (daha küçük hareket yeterli olur)
        self.min_shake_dist = 150 - (level * 12) 
        
        # Git-Gel sayısı
        if level >= 8: self.required_shakes = 2 
        elif level <= 3: self.required_shakes = 5 
        else: self.required_shakes = 3 
        
        logging.info(f"🎚️ Hassasiyet: {level} (Mesafe: {self.min_shake_dist}px)")

    def start(self):
        if self._running: return
        self._running = True
        threading.Thread(target=self._run_keyboard_listener, daemon=True).start()
        threading.Thread(target=self._run_mouse_listener, daemon=True).start()
        logging.info("🎧 Handler Başladı (Safe Shake Aktif)")

    # --- MOUSE DİNLEYİCİSİ ---
    def _run_mouse_listener(self):
        try:
            with mouse.Listener(on_move=self.on_move, on_click=self.on_click) as listener:
                listener.join()
        except Exception as e:
            logging.error(f"⚠️ Mouse Listener Başlatılamadı: {e}")

    def on_click(self, x, y, button, pressed):
        if button == mouse.Button.left:
            self.left_mouse_pressed = pressed
            
        # Tıklama durumu değiştiğinde sayacı sıfırla
        self.shake_count = 0
        self.accumulated_distance = 0
        self.current_direction = 0

    def on_move(self, x, y):
        # 🖱️ 1. TETİKLEYİCİ KONTROLÜ: Sol Tık Basılı mı?
        # Sadece Sol Tık yeterli (Alt tuşuna gerek yok)
        if not self.left_mouse_pressed:
            return

        current_time = time.time()
        
        # 0.5 saniye hareketsiz kalırsan her şeyi sıfırla
        if current_time - self.shake_reset_time > 0.5:
            self.shake_count = 0
            self.accumulated_distance = 0
            self.current_direction = 0  
            self.shake_reset_time = current_time
            self.last_x = x
            return

        diff_x = x - self.last_x
        self.last_x = x 
        self.shake_reset_time = current_time 
        
        if abs(diff_x) < 2: return 
        
        # Hareketin Yönü (1: Sağ, -1: Sol)
        new_direction = 1 if diff_x > 0 else -1
        
        # --- ANA MANTIK ---
        if new_direction == self.current_direction:
            self.accumulated_distance += abs(diff_x)
        else:
            if self.accumulated_distance >= self.min_shake_dist:
                self.shake_count += 1
                logging.debug(f"Yön Değişimi! Shake: {self.shake_count} (Mesafe: {self.accumulated_distance}px)")
                
                if self.shake_count >= self.required_shakes:
                    logging.info("👋 Shake Algılandı! (Click + Shake)")
                    self.shake_count = 0
                    self.accumulated_distance = 0
                    self.current_direction = 0
                    self.trigger_snip_callback()
                    return

            self.accumulated_distance = abs(diff_x)
            self.current_direction = new_direction

    # --- KLAVYE DİNLEYİCİSİ ---
    def _run_keyboard_listener(self):
        try:
            with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
                listener.join()
        except Exception as e:
            logging.error(f"⚠️ Keyboard Listener Başlatılamadı (Kısayollar Devre Dışı): {e}")

    def on_press(self, key):
        try:
            if key == keyboard.Key.cmd:
                self.cmd_pressed = True
            elif hasattr(key, 'char') and key.char == 'c':
                if self.cmd_pressed:
                    current_time = time.time()
                    if current_time - self.last_c_press_time < 0.5:
                        self.c_press_count += 1
                    else:
                        self.c_press_count = 1
                    self.last_c_press_time = current_time

                    if self.c_press_count == 2:
                        self.c_press_count = 0
                        threading.Thread(target=self.on_activate_text, daemon=True).start()
        except AttributeError: pass

    def on_release(self, key):
        if key == keyboard.Key.cmd:
            self.cmd_pressed = False
            self.c_press_count = 0

    # --- İŞLEME MANTIĞI ---
    def on_activate_text(self):
        time.sleep(0.1)
        raw_text = self.get_clipboard_text()
        if raw_text: self.process_clipboard_content(raw_text)

    def get_clipboard_text(self):
        try:
            if platform.system() == 'Darwin':
                pb = NSPasteboard.generalPasteboard()
                return pb.stringForType_(NSStringPboardType)
        except: return None

    def process_clipboard_content(self, raw_text):
        threading.Thread(target=self._process_text_logic, args=(raw_text,), daemon=True).start()

    def _process_text_logic(self, raw_text):
        try:
            # ⭐ LİMİT KONTROLÜ
            if self.usage_tracker.check_limit_reached():
                self.update_callback(f"❌ Çeviri limitine ulaştınız! (0/{self.usage_tracker.limit} kaldı)")
                return

            text = RE_SPACES.sub(' ', RE_NEWLINES.sub(' ', RE_HYPHEN.sub('', raw_text))).strip()
            self.move_window_callback()
            self.update_callback(None)
            self.update_callback({"source_text": text})

            cached = self.db.get_translation(text)
            if cached:
                self.update_callback(cached)
                self.update_callback({"finished": True})
                # Cache'den de gelse sayıyoruz (Tercihe bağlı, ama genelde sayılır)
                self.usage_tracker.increment()
                return

            full = ""
            for chunk in self.api.translate_text_stream(text):
                full += chunk
                self.update_callback({"chunk": chunk})
            self.update_callback({"finished": True})
            self.db.add_history(text, full)
            
            # Başarılı çeviri sonrası artır
            self.usage_tracker.increment()
            
        except Exception as e:
            self.update_callback(f"Error: {e}")

    def process_image(self, image_bytes):
        threading.Thread(target=self._process_image_logic, args=(image_bytes,), daemon=True).start()

    def _process_image_logic(self, image_bytes):
        try:
            # ⭐ LİMİT KONTROLÜ
            if self.usage_tracker.check_limit_reached():
                self.update_callback(f"❌ Çeviri limitine ulaştınız! (0/{self.usage_tracker.limit} kaldı)")
                return

            self.update_callback(None)
            self.update_callback({"source_text": "[Görsel İşleniyor...]"})
            # Stream Buffer Logic
            buffer = ""
            is_translation_started = False
            
            for chunk in self.api.translate_image_stream(image_bytes):
                if not is_translation_started:
                    buffer += chunk
                    if "###TRANSLATION###" in buffer:
                        # Split source and translation
                        parts = buffer.split("###TRANSLATION###")
                        source_part = parts[0].replace("###SOURCE###", "").strip()
                        
                        # Update Source Text UI
                        if source_part:
                            self.update_callback({"source_text": source_part})
                        
                        # Process the remaining part as translation
                        if len(parts) > 1 and parts[1]:
                            self.update_callback({"chunk": parts[1]})
                        
                        is_translation_started = True
                        buffer = "" # Clear buffer
                else:
                    # Direct stream for translation
                    self.update_callback({"chunk": chunk})

            # Eğer loop bitti ve hala bufferda veri varsa (Translation tag gelmediyse)
            if not is_translation_started and buffer:
                 cleaned = buffer.replace("###SOURCE###", "").strip()
                 if cleaned:
                     self.update_callback({"source_text": cleaned}) # Sadece source varmış gibi davran
            self.update_callback({"finished": True})
            
            # ⭐ Başarılı görsel çeviri sonrası artır
            self.usage_tracker.increment()
        except Exception as e:
            self.update_callback(f"Image Error: {e}")

    @pyqtSlot(str, str)
    def process_refine_request(self, source, current):
        threading.Thread(target=self._refine_logic, args=(source, current), daemon=True).start()
    
    def _refine_logic(self, source, current):
        try:
            self.update_callback({"clear_translation": True})
            for chunk in self.api.refine_text_stream(source, current):
                self.update_callback({"chunk": chunk})
            self.update_callback({"finished": True})
        except Exception as e:
            self.update_callback(f"Error: {e}")
