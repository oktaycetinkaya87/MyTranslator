
from main import MainApp
app_instance = MainApp()
count = app_instance.popup.refine_requested.receivers(app_instance.popup.refine_requested)
print(f"Connection Count: {count}")
