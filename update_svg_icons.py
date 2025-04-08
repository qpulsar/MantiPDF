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
# icon name
icon_name = 'print.svg'
# SVG dosyasının yolu
svg_path = os.path.join(os.path.dirname(__file__), 'gui', 'icons', icon_name)
icons_dir = os.path.join(os.path.dirname(__file__), 'gui', 'icons')

print(f"SVG dosyası: {svg_path}")
print(f"İkonlar dizini: {icons_dir}")

# SVG dosyasını oku ve parse et
tree = ET.parse(svg_path)
root = tree.getroot()

# Her tema için SVG dosyasını düzenle ve kaydet
for tema_adi, tema_rengi in tema_renkleri.items():
    # Tema klasörünü oluştur (eğer yoksa)
    tema_klasoru = os.path.join(icons_dir, tema_adi)
    if not os.path.exists(tema_klasoru):
        os.makedirs(tema_klasoru)
        print(f"{tema_adi} klasörü oluşturuldu.")
    
    # SVG dosyasını kopyala
    hedef_svg = os.path.join(tema_klasoru,icon_name)
    
    # Yeni bir ağaç oluştur (her tema için ayrı bir kopya)
    tema_tree = ET.parse(svg_path)
    tema_root = tema_tree.getroot()
    
    # secondary path elementini bul ve rengini güncelle
    secondary_path = tema_root.find(".//*[@id='secondary']")
    if secondary_path is not None:
        # Tema rengini SVG fill özelliğine uygula
        secondary_path.set('style', f"fill: {tema_rengi};")
        print(f"{tema_adi} teması için renk {tema_rengi} olarak ayarlandı.")
    else:
        print(f"HATA: {tema_adi} teması için secondary path bulunamadı!")
    
    # Güncellenmiş SVG'yi kaydet
    tema_tree.write(hedef_svg, encoding='utf-8', xml_declaration=True)
    print(f"{tema_adi} teması için {icon_name} güncellendi: {hedef_svg}")

print("\nTüm temalar için SVG dosyaları başarıyla güncellendi.")