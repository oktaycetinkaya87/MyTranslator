
from PIL import Image, ImageDraw
import os

def create_handle_icon():
    # Boyut: 24x12 (Yükseklik biraz artırıldı ki rahat görünsün)
    width = 24
    height = 12
    
    # Şeffaf zeminli yeni resim
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Nokta rengi (Gri)
    dot_color = (180, 180, 180, 255)
    
    # 3 Nokta (Merkezde)
    # Y koordinatı ortası: height // 2 = 6
    # Nokta yarıçapı: 1.5px (çap 3px)
    
    cy = height // 2
    cx = width // 2
    
    # Noktalar arası mesafe
    gap = 5
    
    # Sol Nokta
    draw.ellipse((cx - gap - 1, cy - 1, cx - gap + 1, cy + 1), fill=dot_color)
    # Orta Nokta
    draw.ellipse((cx - 1, cy - 1, cx + 1, cy + 1), fill=dot_color)
    # Sağ Nokta
    draw.ellipse((cx + gap - 1, cy - 1, cx + gap + 1, cy + 1), fill=dot_color)
    
    # Kaydet
    assets_dir = os.path.join(os.getcwd(), 'assets')
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
        
    save_path = os.path.join(assets_dir, 'splitter_handle.png')
    img.save(save_path)
    print(f"✅ Icon created: {save_path}")

if __name__ == "__main__":
    create_handle_icon()
