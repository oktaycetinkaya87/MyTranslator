import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.api_service import APIService

def test_real_api():
    print("⏳ Initializing APIService with Gemini 3 Flash...")
    api = APIService()
    
    text_to_translate = "Artificial Intelligence is evolving rapidly."
    print(f"📤 Sending request: '{text_to_translate}'")
    
    result = api.translate_text(text_to_translate)
    
    print("\n✅ Response Received:")
    print(result)
    
    if result and "translation" in result:
        print("\n🎉 SUCCESS: Translation and JSON parsing worked!")
    else:
        print("\n❌ FAILURE: Response format incorrect.")

if __name__ == "__main__":
    test_real_api()
