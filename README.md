# MantıPDF

> **"PDF’ye lezzet katan editör."**

![MantıPDF Logo](resources/splash.png)

## 🥟 Nedir?

**MantıPDF**, PDF dosyalarınızı görüntülemenizi, düzenlemenizi ve yönetmenizi sağlayan modern, kullanıcı dostu ve açık kaynaklı bir masaüstü uygulamasıdır. İsmi, sunduğu temel özelliklerin baş harflerinden oluşur:

- **M**anipüle et
- **A**not al (Annotation)
- **N**ot Tut
- **T**asarla
- **İ**ncele

Kısaca: **MANTI** 🥟

---

## ✨ Özellikler

### 🛠️ Manipülasyon
- **PDF Birleştirme:** Birden fazla PDF dosyasını tek bir dosyada birleştirin.
- **Klasör Birleştirme:** Bir klasördeki tüm PDF'leri hızlıca birleştirin.
- **PDF Bölme:** Dosyaları sayfa sayfa veya belirli aralıklarla bölün.
- **Sayfa Yönetimi:** Sayfaları döndürün (Sola, Sağa, 180°), yeni boş sayfa ekleyin veya mevcut sayfaları silin.
- **Sayfa Sıralama:** Sürükle-bırak yöntemiyle veya araç çubuğu butonlarıyla sayfaların sırasını değiştirin.

### 🖋️ Not Alma & Çizim
- **Metin Ekleme:** PDF üzerine özelleştirilebilir metinler ekleyin (Font, renk, boyut seçimi).
- **Şekil Çizme:** Çizgi, Daire, Kare gibi şekiller ekleyin.
- **Vurgulama:** Önemli metinlerin üzerini fosforlu kalemle çizin.
- **Serbest Çizim:** Kalem aracıyla PDF üzerine serbest çizimler yapın.
- **Damga (Stamp):** Önceden tanımlı "ONAYLANDI", "GİZLİ", "TASLAK" gibi damgaları tek tıkla ekleyin.

### 🎨 Tasarım & Arayüz
- **Modern Arayüz:** Göz yormayan, şık **Dark Theme** (Koyu Tema) desteği.
- **Dinamik Temalar:** Farklı renk seçenekleriyle arayüzü kişiselleştirin.
- **Gelişmiş Görüntüleme:** Yakınlaştırma, uzaklaştırma, genişliğe sığdırma ve tam sayfa görüntüleme modları.

### 🔎 İnceleme
- **Detaylı Gezinti:** Küçük resim (thumbnail) görünümü ile sayfalar arasında hızlıca geçiş yapın.
- **Özellik Düzenleme:** Seçili nesnelerin özelliklerini (renk, kalınlık, dolgu, font vb.) dinamik özellik çubuğundan anında değiştirin.

---

## 🚀 Kurulum

Projeyi bilgisayarınıza klonlayın ve gerekli kütüphaneleri yükleyin:

1. **Repoyu Klonlayın:**
   ```bash
   git clone https://github.com/qpulsar/MantiPDF.git
   cd MantiPDF
   ```

2. **Sanal Ortam Oluşturun (Önerilen):**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Mac/Linux için
   # .venv\Scripts\activate   # Windows için
   ```

3. **Gereksinimleri Yükleyin:**
   ```bash
   pip install -r requirements.txt
   ```

---

## ▶️ Kullanım

Uygulamayı başlatmak için ana dosya olan `main.py` dosyasını çalıştırın:

```bash
python main.py
```

Uygulama açılışında sizi şık bir karşılama ekranı (Splash Screen) karşılayacaktır.

---

## 🛠️ Teknoloji Yığını

Bu proje aşağıdaki teknolojiler kullanılarak geliştirilmiştir:

- **Python 3.10+**
- **PyQt6:** Güçlü ve modern GUI çerçevesi.
- **PyMuPDF (fitz):** PDF işleme ve render motoru.
- **qt-material:** Materyal tasarım temaları için.

---

## 👨‍💻 Geliştirici

**Mehmet Emin Korkusuz**

- 🌐 Web: [korkusuz.gen.tr](https://korkusuz.gen.tr)
- 🐙 GitHub: [@qpulsar](https://github.com/qpulsar)

---

> *MantıPDF, kodlamanın lezzetli halidir.* 🥟
