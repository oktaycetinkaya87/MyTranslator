from PIL import Image

def make_transparent():
    img_path = 'assets/logo.png'
    save_path = 'assets/logo_transparent.png'
    
    img = Image.open(img_path)
    # 1. Convert to RGBA
    img = img.convert("RGBA")
    
    # 2. Make Transparent (Aggressive)
    data = img.getdata()
    newData = []
    for item in data:
        # Check if pixel is "close enough" to white (Background)
        if item[0] > 200 and item[1] > 200 and item[2] > 200:
            newData.append((255, 255, 255, 0)) 
        else:
            newData.append(item)
    img.putdata(newData)
    
    # 3. CROP Implementation (maximize visual size)
    # GetBoundingBox returns the box of non-zero alpha pixels
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
        print(f"✂️ Cropped to content: {bbox}")
    
    # 4. Resize to high resolution (128x128) for safe scaling
    img = img.resize((128, 128), Image.Resampling.LANCZOS)
    
    img.save(save_path, "PNG")
    print(f"✅ Created maximized logo: {save_path}")

if __name__ == "__main__":
    make_transparent()
