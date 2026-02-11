from PIL import Image

def process_icon():
    input_path = 'assets/tray_ikon.png'
    output_path = 'assets/tray_icon_final.png'
    
    try:
        img = Image.open(input_path).convert("RGBA")
        
        # Target size (Retina "Big" Tray Icon)
        target_size = (88, 88)
        
        # Calculate aspect ratio preserving resize
        img.thumbnail(target_size, Image.Resampling.LANCZOS)
        
        # Create new square background (transparent)
        new_img = Image.new("RGBA", target_size, (0, 0, 0, 0))
        
        # Paste centered
        x_offset = (target_size[0] - img.width) // 2
        y_offset = (target_size[1] - img.height) // 2
        
        new_img.paste(img, (x_offset, y_offset))
        
        new_img.save(output_path)
        print(f"✅ Processed icon saved to: {output_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    process_icon()
