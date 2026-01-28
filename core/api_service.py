import os
import json
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

        # FORCE REST TRANSPORT (Fixes macOS gRPC lag)
        self.client = genai.Client(
            api_key=self.api_key,
            http_options={'api_version': 'v1beta'}
        )

        self.model_name = "gemini-3-flash-preview"
        
        # 2026 STANDARD: JSON SCHEMA DEFINITION
        self.response_schema = {
            "type": "OBJECT",
            "properties": {
                "translation": {"type": "STRING", "description": "Turkish translation (Academic)."},
                "terms": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"},
                    "description": "Extracted technical terms."
                }
            },
            "required": ["translation", "terms"]
        }

        self.sys_instruction = "Translate text to Turkish (Academic). Extract terms."
        
        self.generation_config = types.GenerateContentConfig(
            temperature=0.3,
            response_mime_type="application/json",
            response_schema=self.response_schema, # Using Schema instead of Regex
            max_output_tokens=8192,
            system_instruction=self.sys_instruction
        )

    def translate_text(self, text):
        if not text: return None
        try:
            # Generate content (Guaranteed JSON due to Schema)
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=text,
                config=self.generation_config
            )
            # Safe parsing
            return json.loads(response.text)
        except Exception as e:
            logging.error(f"❌ API Error: {e}")
            return {"translation": f"Hata: {str(e)}", "terms": []}
