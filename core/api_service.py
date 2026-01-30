import os
import logging
import threading
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

class APIService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logging.error("❌ API Key missing!")
            return

        self.client = genai.Client(
            api_key=self.api_key,
            http_options={'api_version': 'v1beta'}
        )

        self.model_name = "gemini-2.0-flash" # Veya gemini-1.5-flash
        
        # LATENCY OPTİMİZASYONU 1: System Prompt'u Token Tasarrufu İçin Kısalttık
        # Eski: "Sen akademik bir çevirmensin..." (~20 token)
        # Yeni: "TR Çeviri. Akademik. Sadece metin." (~6 token) -> Etki aynı, hız daha yüksek.
        self.stream_config = types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=8192,
            system_instruction="Translate to Turkish. Academic style. Output only translation."
        )

    def warmup(self):
        """
        LATENCY OPTİMİZASYONU 2: Connection Warm-up
        İlk bağlantı maliyetini (SSL Handshake) uygulama açılışında öder.
        Kullanıcı ilk çevirisini yaparken hat hazır olur.
        """
        def _warmup_task():
            try:
                logging.info("🔥 API Isınma turu başladı...")
                # Tek tokenlık boş bir istek
                self.client.models.generate_content(
                    model=self.model_name,
                    contents="Hi",
                    config=types.GenerateContentConfig(max_output_tokens=1)
                )
                logging.info("✅ API Isındı ve hazır!")
            except Exception as e:
                logging.warning(f"Isınma hatası (Önemli değil): {e}")

        # Ana akışı bloklamamak için thread içinde çalıştır
        threading.Thread(target=_warmup_task, daemon=True).start()

    def translate_text_stream(self, text):
        if not text: return
        try:
            response = self.client.models.generate_content_stream(
                model=self.model_name,
                contents=text,
                config=self.stream_config
            )
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logging.error(f"❌ API Stream Error: {e}")
            yield f" [Hata: {str(e)}]"
