import os
import sys
from xml.etree import ElementTree as ET

# Tema renkleri - gerçek uygulamada kullanılan temalar
tema_renkleri = {
    'dark_teal': '#009688',
    'dark_blue': '#2979ff',
    'dark_cyan': '#00bcd4',
    'dark_lightgreen': '#8bc34a',
    'dark_pink': '#e91e63',
    'dark_purple': '#9c27b0',
    'dark_red': '#f44336',
    'dark_yellow': '#ffeb3b',
    'dark_amber': '#ffc107',
    'dark_medical': '#00b8d4',
    'light_blue': '#2979ff',
    'light_cyan': '#00bcd4',
    'light_teal': '#009688',
    'light_yellow': '#ffeb3b',
    'light_amber': '#ffc107',
    'light_orange': '#ff9800',
    'light_pink': '#e91e63',
    'light_purple': '#9c27b0',
    'light_red': '#f44336',
    'light_lightgreen': '#8bc34a',
    'light_blue_500': '#2196f3',
    'light_cyan_500': '#00bcd4',
    'light_teal_500': '#009688',
    'light_red_500': '#f44336',
    'light_pink_500': '#e91e63',
    'light_purple_500': '#9c27b0',
    'light_lightgreen_500': '#8bc34a'
}

icons_dir = os.path.join(os.path.dirname(__file__), 'gui', 'icons')

# Tüm SVG dosyalarını bul
svg_files = [f for f in os.listdir(icons_dir) if f.endswith('.svg') and os.path.isfile(os.path.join(icons_dir, f))]

print(f"İkonlar dizini: {icons_dir}")
print(f"İşlenecek {len(svg_files)} ikon bulundu.")

for icon_name in svg_files:
    svg_path = os.path.join(icons_dir, icon_name)
    
    # Her tema için SVG dosyasını düzenle ve kaydet
    for tema_adi, tema_rengi in tema_renkleri.items():
        # Tema klasörünü oluştur (eğer yoksa)
        tema_klasoru = os.path.join(icons_dir, tema_adi)
        if not os.path.exists(tema_klasoru):
            os.makedirs(tema_klasoru)
        
        hedef_svg = os.path.join(tema_klasoru, icon_name)
        
        try:
            tree = ET.parse(svg_path)
            root = tree.getroot()
            
            # secondary path elementini bul ve rengini güncelle
            secondary_path = root.find(".//*[@id='secondary']")
            if secondary_path is not None:
                secondary_path.set('style', f"fill: {tema_rengi};")
            
            # Güncellenmiş SVG'yi kaydet
            tree.write(hedef_svg, encoding='utf-8', xml_declaration=True)
        except Exception as e:
            print(f"HATA: {icon_name} ({tema_adi}) işlenirken hata: {e}")

print("\nTüm temalar için SVG dosyaları başarıyla güncellendi.")