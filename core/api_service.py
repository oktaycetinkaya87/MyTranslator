import os
import logging
import threading
from google import genai
from google.genai import types
from dotenv import load_dotenv

from core.prompts import REFINE_SYSTEM_PROMPT, build_refine_request

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

        # ⚡️ GÜNCEL HIZ MOTORU: Gemini 2.5 Flash-Lite
        # Ultra düşük gecikme (latency) ve yüksek işlem hacmi için optimize edilmiş
        # en kararlı ve hızlı sürümdür.
        self.model_name = "gemini-2.5-flash-lite" 
        
        # ⚡️ OPTİMİZASYON: Token Limiti & Sade Prompt
        # 2.5 Flash-Lite'ın varsayılan limiti çok yüksektir (65k+), ancak
        # biz anlık hız için 2048 token (yaklaşık 1500 kelime) ile sınırlandırıyoruz.
        self.stream_config = types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=2048,
            system_instruction="Translate to Academic Turkish (if input not TR) or Academic English (if TR). No explanations."
        )

        # Warmup: İlk açılıştaki SSL el sıkışmasını yapar.
        self.warmup()

    def warmup(self):
        """
        WARMUP (Isınma)
        Uygulama ilk açıldığında Google sunucularına "Selam" vererek
        SSL/TLS tünelini kazar. İlk işlemin yavaş olmasını engeller.
        """
        def _warmup_task():
            try:
                logging.info(f"🔥 [Warmup] {self.model_name} motoru ısıtılıyor...")
                self.client.models.generate_content(
                    model=self.model_name,
                    contents="Hi",
                    config=types.GenerateContentConfig(max_output_tokens=1)
                )
                logging.info("✅ [Warmup] Motor ısındı ve hazır!")
            except Exception as e:
                logging.warning(f"Isınma hatası (Önemli değil): {e}")

        threading.Thread(target=_warmup_task, daemon=True).start()

    def refine_text_stream(self, source_text, current_text):
        """Çeviriyi, anlamını değiştirmeden akademik üslup açısından düzeltir."""
        if not current_text or not current_text.strip(): return

        refine_config = types.GenerateContentConfig(
            temperature=0.4,
            max_output_tokens=2048,
            system_instruction=REFINE_SYSTEM_PROMPT
        )

        try:
            response = self.client.models.generate_content_stream(
                model=self.model_name,
                contents=build_refine_request(source_text, current_text),
                config=refine_config
            )
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logging.error(f"❌ Refine Error: {e}")
            yield f" [Error: {str(e)}]"

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

    def translate_image_stream(self, image_bytes):
        if not image_bytes:
            logging.error("❌ image_bytes BOŞ!")
            return
        
        try:
            # DEBUG LOGLARI
            logging.info(f"🔍 Görüntü Alındı - Boyut: {len(image_bytes)} bytes")
            logging.info(f"🔍 Veri Tipi: {type(image_bytes)}")
            
            prompt = """
            You are a professional academic translator.
            
            STRICT INSTRUCTION:
            1. EXTRACT the text from the image exactly as it appears.
            2. DETECT the language of the extracted text.
            3. TRANSLATE the text:
               - If Turkish -> to Academic English.
               - If NOT Turkish -> to Academic Turkish.
            
            OUTPUT FORMAT (Strictly follow this structure):
            ###SOURCE###
            (The extracted source text here)
            ###TRANSLATION###
            (The translation here)
            """
            
            # ✅ DÜZELTME: Gemini 2.x API doğru formatı
            image_part = types.Part(
                inline_data=types.Blob(
                    mime_type="image/png",
                    data=image_bytes
                )
            )
            
            logging.info("✅ Part objesi oluşturuldu, API çağrısı başlıyor...")
            
            response = self.client.models.generate_content_stream(
                model=self.model_name,
                contents=[prompt, image_part],
                config=self.stream_config
            )
            
            chunk_count = 0
            for chunk in response:
                if chunk.text:
                    chunk_count += 1
                    logging.info(f"📦 Chunk {chunk_count} alındı")
                    yield chunk.text
            
            logging.info(f"✅ Çeviri tamamlandı - Toplam {chunk_count} chunk")
            
        except Exception as e:
            logging.error(f"❌ API Image Stream Error: {e}")
            import traceback
            logging.error(traceback.format_exc())
            yield f" [Hata: {str(e)}]"
