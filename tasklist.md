# MantiPDF Editor - Task List

## Core Functionality
- [x] Proje yapısını oluştur (klasörler: core, gui, resources)
- [x] Temel PyQt6 penceresini oluştur (`gui/main_window.py`)
- [x] qt-material temasını entegre et ve tema değiştirme mekanizması ekle (Açık/Koyu dahil)
- [x] PyMuPDF kullanarak PDF dosyası açma (`core/pdf_handler.py`, `gui/main_window.py`)
- [x] PDF sayfasını görüntüleme (`gui/pdf_viewer.py`)
- [x] Sayfa önizlemelerini gösterme (`gui/thumbnail_view.py`)
- [x] Kaydetme (`core/pdf_handler.py`, `gui/main_window.py`)
- [x] Farklı Kaydetme (`core/pdf_handler.py`, `gui/main_window.py`)

## Page Operations
- [x] Sayfa ekle (boş sayfa) (`core/pdf_handler.py`)
- [x] Sayfa sil (`core/pdf_handler.py`)
- [x] Sola döndür (`core/pdf_handler.py`)
- [x] Sağa döndür (`core/pdf_handler.py`)
- [x] Ters döndür (180 derece) (`core/pdf_handler.py`)

## File Operations
- [x] PDF Birleştir (mevcut olana başka bir PDF ekle) (`core/pdf_handler.py`)
- [ ] PDF Böl (diyalog ile seçenek sun) (`core/pdf_handler.py`)
- [ ] Yazdır (`gui/main_window.py` veya `core/pdf_handler.py` - sistem yazdırma diyalogu)
- [ ] Resim olarak kaydet (mevcut sayfayı) (`core/pdf_handler.py`)
- [ ] Metin çıkart (mevcut sayfadan) (`core/pdf_handler.py`)

## View Operations
- [ ] Zoom In (`gui/pdf_viewer.py`)
- [ ] Zoom Out (`gui/pdf_viewer.py`)
- [ ] Zoom Fit (tam sığdırma) (`gui/pdf_viewer.py`)
- [ ] Zoom Fix (genişliğe sığdır) (`gui/pdf_viewer.py`)

## Editing/Annotation
- [ ] Not ekle (yapışkan not gibi?)
- [ ] Text Ekle
- [ ] Çizgi Ekle
- [ ] Vurgula (Highlight)
- [ ] Daire Ekle
- [ ] Stampa ekle (kullanıcının seçtiği resim)

## UI/UX
- [x] Araç çubuklarını oluştur (`gui/toolbar_manager.py`)
- [x] Menüleri oluştur (`gui/main_window.py`)
- [x] Durum çubuğunu ekle (örn: sayfa numarası, zoom seviyesi) (`gui/main_window.py`)
- [x] İkonları ayarla (qt-material veya özel)
- [x] Klavye kısayolları ekle
