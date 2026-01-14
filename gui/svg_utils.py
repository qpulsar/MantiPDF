import os
import shutil
from xml.etree import ElementTree as ET
from qt_material import get_theme

def update_svg_colors(svg_path, theme_name):
    """SVG dosyasındaki renkleri tema rengine göre günceller.
    
    Args:
        svg_path (str): SVG dosyasının yolu
        theme_name (str): Tema adı (örn. 'dark_teal')
        
    Returns:
        str: Güncellenmiş SVG içeriği
    """
    try:
        # Tema adını doğru formatta kullan (get_theme fonksiyonu tema adını uzantısız bekliyor)
        # Eğer tema adı .xml uzantısı içeriyorsa, kaldır
        if theme_name.endswith('.xml'):
            theme_name = theme_name[:-4]
        
        # Tema dosyasının varlığını kontrol et
        import qt_material
        qt_material_path = qt_material.__path__[0]
        theme_file_path = os.path.join(qt_material_path, 'themes', f"{theme_name}.xml")
        
        if not os.path.exists(theme_file_path):
            return None
            
        # Tema verilerini al
        theme_data = get_theme(theme_name)
        if not theme_data or 'primaryColor' not in theme_data:
            return None
            
        # SVG dosyasını oku ve parse et
        tree = ET.parse(svg_path)
        root = tree.getroot()
        
        # secondary path elementini bul ve rengini güncelle
        secondary_path = root.find(".//*[@id='secondary']")
        if secondary_path is not None:
            # Tema rengini SVG fill özelliğine uygula
            primary_color = theme_data.get('primaryColor')
            if primary_color:
                secondary_path.set('style', f"fill: {primary_color};")
            else:
                print(f"Tema içinde 'primaryColor' bulunamadı: {theme_name}")

        # Güncellenmiş SVG'yi string olarak döndür
        return ET.tostring(root, encoding='unicode')

    except Exception as e:
        print(f"SVG güncelleme hatası: {e}")
        return None

def get_themed_icon_path(original_icon_path, theme_name):
    """Belirli bir tema için ikon yolunu döndürür.
    Eğer tema için ikon yoksa None döndürür.
    
    Args:
        original_icon_path (str): Orijinal ikon dosyasının yolu
        theme_name (str): Tema adı
        
    Returns:
        str: Tema için ikon yolu veya None
    """
    if theme_name.endswith('.xml'):
        theme_name = theme_name[:-4]
        
    # Orijinal dosya adını ve dizinini al
    icon_dir = os.path.dirname(original_icon_path)
    icon_filename = os.path.basename(original_icon_path)
    
    # Tema dizini yolu
    theme_dir = os.path.join(icon_dir, theme_name)
    themed_icon_path = os.path.join(theme_dir, icon_filename)
    
    # Tema için ikon varsa yolunu döndür
    if os.path.exists(themed_icon_path):
        return themed_icon_path
    
    return None

def create_themed_icons(icons_dir):
    """Tüm temalar için ikon kopyaları oluşturur.
    
    Args:
        icons_dir (str): İkonların bulunduğu dizin
    """
    # Mevcut temaları al
    import qt_material
    qt_material_path = qt_material.__path__[0]
    themes_dir = os.path.join(qt_material_path, 'themes')
    themes = [theme.replace('.xml', '') for theme in os.listdir(themes_dir) if theme.endswith('.xml')]
    
    # Her tema için dizin oluştur ve ikonları kopyala
    for theme_name in themes:
        theme_dir = os.path.join(icons_dir, theme_name)
        
        # Tema dizini yoksa oluştur
        if not os.path.exists(theme_dir):
            os.makedirs(theme_dir)
        
        # Orijinal SVG dosyalarını tema dizinine kopyala ve renklerini güncelle
        for filename in os.listdir(icons_dir):
            if filename.endswith('.svg') and os.path.isfile(os.path.join(icons_dir, filename)):
                original_svg_path = os.path.join(icons_dir, filename)
                themed_svg_path = os.path.join(theme_dir, filename)
                
                # SVG'yi tema rengine göre güncelle
                updated_svg = update_svg_colors(original_svg_path, theme_name)
                if updated_svg:
                    with open(themed_svg_path, 'w', encoding='utf-8') as f:
                        f.write(updated_svg)

def get_icon_for_theme(icon_name, theme_name, icons_dir):
    """Belirli bir tema için ikon dosyasının tam yolunu döndürür.
    Eğer tema için özel ikon yoksa, orijinal ikonu döndürür.
    
    Args:
        icon_name (str): İkon dosyasının adı (örn. 'open.svg')
        theme_name (str): Tema adı
        icons_dir (str): İkonların bulunduğu ana dizin
        
    Returns:
        str: İkon dosyasının tam yolu
    """
    if theme_name.endswith('.xml'):
        theme_name = theme_name[:-4]
    
    # Tema dizinindeki ikon yolu
    theme_dir = os.path.join(icons_dir, theme_name)
    themed_icon_path = os.path.join(theme_dir, icon_name)
    
    # Tema için ikon varsa onu döndür, yoksa orijinal ikonu döndür
    if os.path.exists(themed_icon_path):
        return themed_icon_path
    else:
        return os.path.join(icons_dir, icon_name)
