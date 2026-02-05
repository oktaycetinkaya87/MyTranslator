import os
import logging
import time
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

        # 🛡️ ÇİFTE KORUMA (Latency Önleyici)
        # Warmup: İlk açılıştaki SSL el sıkışmasını yapar.
        # Heartbeat: Bağlantıyı sürekli canlı tutar.
        self.warmup()
        self._start_heartbeat()

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

    def _start_heartbeat(self):
        """
        HEARTBEAT (Kalp Atışı)
        Siz çalışmasanız bile 45 saniyede bir boş sinyal göndererek
        Google ile olan hattın 'soğumasını' ve kapanmasını engeller.
        """
        def _beat():
            # Warmup ile çakışmaması için 5 saniye bekle
            time.sleep(5) 
            logging.info("💓 [Heartbeat] Servisi devrede.")
            
            while True:
                # 45 saniyede bir (Google genelde 60sn'de hattı keser, biz 45 ile güvenli oynuyoruz)
                time.sleep(45)
                try:
                    # Boş bir ping at (Token maliyeti yok gibidir)
                    self.client.models.generate_content(
                        model=self.model_name,
                        contents=".",
                        config=types.GenerateContentConfig(max_output_tokens=1)
                    )
                    # Logları kirletmemek için pass geçiyoruz, arka planda sessizce çalışır.
                except Exception:
                    pass 

        threading.Thread(target=_beat, daemon=True).start()

    # ✨ YENİ FONKSİYON: Humanize
    def humanize_text_stream(self, source_text, current_text):
        if not source_text: return
        
        HUMANIZE_SYSTEM_PROMPT = """
You are an expert academic editor. Your task is to rewrite the 'Current Text' to make it indistinguishable from human writing, specifically to bypass AI detection filters.

Goal: High Perplexity and High Burstiness.
1.  **Perplexity (Complexity):** Avoid predictable word choices. Use varied vocabulary and slightly more complex sentence structures where appropriate for academia.
2.  **Burstiness (Sentence Variation):** AI generates sentences of uniform length. You must vary sentence length significantly. Mix short, punchy sentences with longer, complex compound sentences.

Strict Rules:
-   **CRITICAL:** OUTPUT MUST BE IN THE SAME LANGUAGE AS THE 'Current Text'.
-   **NEVER** translate the text back to the 'Source Reference Text' language.
-   Preserve the original academic meaning 100%.
-   Do NOT be too formal/robotic. Use natural transitions (e.g., "Furthermore," "On the other hand," "Crucially").
-   If 'Current Text' is Turkish -> Output Turkish.
-   If 'Current Text' is English -> Output English.
-   Output ONLY the rewritten text.
"""
        
        humanize_config = types.GenerateContentConfig(
            temperature=0.7, 
            max_output_tokens=2048,
            system_instruction=HUMANIZE_SYSTEM_PROMPT
        )

        user_prompt = f"Source Reference Text:\n{source_text}\n\nCurrent Text:\n{current_text}"
        
        # DEBUG LOG
        logging.critical("\n--- HUMANIZE PROMPT ---")
        logging.critical(f"Source Len: {len(source_text)}")
        logging.critical("-----------------------")

        try:
            response = self.client.models.generate_content_stream(
                model=self.model_name,
                contents=user_prompt,
                config=humanize_config
            )
            for chunk in response:
                if chunk.text: 
                    logging.critical(f"DEBUG CHUNK: {chunk.text[:20]}...") # Gelen veriyi gör
                    yield chunk.text
        except Exception as e:
            logging.error(f"❌ Humanize Error: {e}")
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
