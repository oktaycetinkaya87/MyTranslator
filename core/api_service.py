import os
import logging
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

        # FORCE REST TRANSPORT (macOS gRPC lag fix)
        self.client = genai.Client(
            api_key=self.api_key,
            http_options={'api_version': 'v1beta'}
        )

        # KULLANICI TERCİHİ: SABİT MODEL
        # Bu model ismi asla değiştirilmeyecek.
        self.model_name = "gemini-3-flash-preview"
        
        # HIZLI MOD İÇİN SADE CONFIG (JSON Schema YOK)
        # Latency'yi düşürmek için modelin sadece metin üretmesini istiyoruz.
        self.stream_config = types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=8192,
            system_instruction="Sen akademik bir çevirmensin. Verilen metni doğrudan Türkçe'ye çevir. Açıklama yapma, sadece çeviriyi ver."
        )

    def translate_text_stream(self, text):
        """
        Generator function that yields translation chunks in real-time.
        """
        if not text: return
        
        try:
            # Use generate_content_stream explicitly
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
