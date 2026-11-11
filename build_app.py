import os
import sys
import shutil
import subprocess

# Configuration
APP_NAME = "MyTranslator"
MAIN_SCRIPT = "main.py"

# Detect OS
IS_WINDOWS = sys.platform.startswith('win')
IS_MACOS = sys.platform == 'darwin'

# OS Specific Config
if IS_WINDOWS:
    ICON_FILE = os.path.join("assets", "app_icon.ico")
    ADD_DATA_SEP = ";"
else:
    ICON_FILE = os.path.join("assets", "app_icon.icns")
    ADD_DATA_SEP = ":"

def build():
    print(f"🔨 Building {APP_NAME} on {sys.platform}...")

    try:
        # Clean previous builds
        if os.path.exists("build"): shutil.rmtree("build")
        if os.path.exists("dist"): shutil.rmtree("dist")
        
        # PyInstaller Command Construction
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--noconfirm",
            "--onefile",
            "--windowed",
            "--name", APP_NAME,
            f"--add-data", f"assets{ADD_DATA_SEP}assets",
            "--hidden-import", "PIL",
            MAIN_SCRIPT
        ]

        # Conditional Hidden Imports
        if IS_MACOS:
            cmd.extend([
                "--hidden-import", "pynput.keyboard._darwin",
                "--hidden-import", "pynput.mouse._darwin"
            ])
        elif IS_WINDOWS:
            cmd.extend([
                "--hidden-import", "pynput.keyboard._win32",
                "--hidden-import", "pynput.mouse._win32"
            ])
        
        # Icon
        if os.path.exists(ICON_FILE):
             cmd.extend(["--icon", ICON_FILE])
        else:
            print(f"⚠️ Icon not found: {ICON_FILE}")

        # Execute
        print(f"🚀 Running: {' '.join(cmd)}")
        subprocess.check_call(cmd)
        
        print(f"✅ Build Successful: dist/{APP_NAME}")

    except Exception as e:
        print(f"❌ Build Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build()
