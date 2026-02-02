try:
    from AppKit import NSPasteboard
    print("✅ AppKit Imported Successfully")
except ImportError as e:
    print(f"❌ AppKit Import Failed: {e}")
except Exception as e:
    print(f"❌ Unexpected Error: {e}")
