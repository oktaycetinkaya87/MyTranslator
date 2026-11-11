
import sys
import os
import time
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from database.db_manager import DatabaseManager
from core.api_service import APIService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def simulate_user_scenarios():
    print("\n🚀 Starting Real User Simulation Scenarios...\n")
    
    # Check Environment
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ ERROR: GEMINI_API_KEY is not set in environment.")
        return

    # 1. Initialize Components
    print("🔹 [Step 1] Initializing Application Components...")
    try:
        db = DatabaseManager(db_name="simulation_test.db")
        # Clear previous simulation data
        db.clear_history()
        
        api = APIService()
        print("✅ Components initialized successfully.")
    except Exception as e:
        print(f"❌ Initialization Failed: {e}")
        return

    # 2. Scenario: Check Translation (Real API Call)
    print("\n🔹 [Step 2] Simulating User Translation Request...")
    test_text = "The quick brown fox jumps over the lazy dog."
    print(f"   Input Text: '{test_text}'")
    
    translated_text = ""
    try:
        print("   Translating...", end="", flush=True)
        # Consume the generator
        chunks = []
        for chunk in api.translate_text_stream(test_text):
            chunks.append(chunk)
            print(".", end="", flush=True)
        translated_text = "".join(chunks)
        print("\n   Output Translation:", translated_text)
        
        if len(translated_text) > 5 and translated_text != test_text:
            print("✅ Translation Scenario: PASS")
        else:
            print("❌ Translation Scenario: FAIL (Output seems invalid)")
    except Exception as e:
        print(f"\n❌ Translation Error: {e}")

    # 3. Scenario: Database History Recording
    print("\n🔹 [Step 3] Simulating History Recording...")
    try:
        if translated_text:
            db.add_history(test_text, translated_text, "Academic")
            
            # Verify record exists
            history = db.get_last_history(limit=1)
            if history and history[0]['original_text'] == test_text:
                print(f"   Saved Record: {history[0]}")
                print("✅ History Recording Scenario: PASS")
            else:
                print("❌ History Recording Scenario: FAIL (Record not found)")
        else:
             print("⚠️ Skipping History test due to translation failure.")
    except Exception as e:
        print(f"❌ Database Error: {e}")

    # 4. Scenario: Refine Request
    print("\n🔹 [Step 4] Simulating 'Refine' Request...")
    try:
        if translated_text:
            print("   Refining...", end="", flush=True)
            refined_chunks = []
            for chunk in api.refine_text_stream(test_text, translated_text):
                refined_chunks.append(chunk)
                print(".", end="", flush=True)
            refined_text = "".join(refined_chunks)
            print("\n   Refined Text:", refined_text)
            
            if len(refined_text) > 5:
                print("✅ Refine Scenario: PASS")
            else:
                print("❌ Refine Scenario: FAIL")
        else:
            print("⚠️ Skipping Refine test due to translation failure.")
    except Exception as e:
        print(f"\n❌ Refine Error: {e}")

    # Cleanup
    if os.path.exists("simulation_test.db"):
        os.remove("simulation_test.db")
        print("\n🧹 Cleanup: Removed test database.")

    print("\n🎉 Simulation Complete.")

if __name__ == "__main__":
    simulate_user_scenarios()
