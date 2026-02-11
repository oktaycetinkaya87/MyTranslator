
from PIL import Image, ImageDraw

def create_app_icon():
    size = (64, 64)
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Simple Cloud Shape
    # Circles
    # Left
    draw.ellipse((10, 20, 30, 40), fill=(0, 150, 255, 255))
    # Right
    draw.ellipse((34, 20, 54, 40), fill=(0, 200, 150, 255))
    # Top
    draw.ellipse((22, 10, 42, 30), fill=(0, 180, 200, 255))
    # Bottom rect to connect
    draw.rectangle((20, 25, 44, 40), fill=(0, 180, 200, 255))
    
    import os
    assets_dir = os.path.join(os.getcwd(), 'assets')
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
        
    save_path = os.path.join(assets_dir, 'app_icon.png')
    img.save(save_path)
    print(f"✅ App Icon created: {save_path}")

    # --- TRAY ICON (Standard MacOS Style) ---
    tray_size = (44, 44) 
    tray_img = Image.new('RGBA', tray_size, (0, 0, 0, 0))
    draw_tray = ImageDraw.Draw(tray_img)
    
    # Draw a simple "T" shape centered
    # Vertical bar
    draw_tray.rectangle((20, 10, 24, 38), fill="black")
    # Horizontal bar
    draw_tray.rectangle((12, 10, 32, 14), fill="black")
    
    # White border for visibility on dark backgrounds
    # (Optional, but good for contrast)
    
    tray_save_path = os.path.join(assets_dir, 'tray_icon.png')
    tray_img.save(tray_save_path)
    print(f"✅ Tray Icon created: {tray_save_path}")

if __name__ == "__main__":
    create_app_icon()
