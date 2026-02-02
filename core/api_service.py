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

        self.model_name = "gemini-3-flash-preview" 
        
        # GÜNCELLENEN KISIM: Daha Sıkı Kurallar
        self.stream_config = types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=8192,
            system_instruction=(
                "You are an expert academic translator. Strictly follow these rules:\n"
                "1. IF the input is in TURKISH -> Translate to ACADEMIC ENGLISH.\n"
                "2. IF the input is in ENGLISH or ANY OTHER LANGUAGE -> Translate to ACADEMIC TURKISH.\n"
                "Output ONLY the translation. Do not add explanations."
            )
        )

    def warmup(self):
        """
        İlk bağlantı maliyetini (SSL Handshake) uygulama açılışında öder.
        """
        def _warmup_task():
            try:
                logging.info("🔥 API Isınma turu başladı...")
                self.client.models.generate_content(
                    model=self.model_name,
                    contents="Hi",
                    config=types.GenerateContentConfig(max_output_tokens=1)
                )
                logging.info("✅ API Isındı ve hazır!")
            except Exception as e:
                logging.warning(f"Isınma hatası (Önemli değil): {e}")

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
