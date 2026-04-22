# MantiPDF AI Entegrasyon Görevleri

## ✅ Tamamlananlar (Yapılanlar)

### Hazırlık ve Güvenlik
- [x] `keyring` ve gerekli AI kütüphanelerinin (`openai`, `anthropic`, `google-generativeai`, `langchain`) `requirements.txt`'ye eklenmesi
- [x] `core/security_manager.py` oluşturulması (API anahtarlarının macOS Keychain'de güvenli saklanması)
- [x] AI Ayarları diyaloğunun (`gui/ai_settings_dialog.py`) oluşturulması (OpenAI, Anthropic, Gemini desteği)

### AI Temel Altyapı
- [x] `core/ai_handler.py` modüler yapısının kurulması
- [x] OpenAI, Anthropic ve Google Gemini sağlayıcı entegrasyonları
- [x] `core/pdf_indexer.py` ile PDF içeriklerinin FAISS vektör veritabanına dizinlenmesi (RAG altyapısı)

### Kullanıcı Arayüzü (GUI) Entegrasyonu
- [x] Ana pencereye AI menüsünün eklenmesi
- [x] AI Assistant yan panelinin (`gui/ai_assistant_dock.py`) oluşturulması (Sohbet ve Hızlı Aksiyonlar)
- [x] PDF Viewer üzerinde metin seçme (Text Selection) özelliği
- [x] Seçili metin üzerinde sağ tık AI aksiyonları (Açıkla, Özetle, Çevir)

### AI Özellikleri - Aşama 1 & 2
- [x] Akıllı özetleme (Tüm belge veya seçili alan)
- [x] Anahtar kavram ve ilişki çıkarımı
- [x] PDF ile Sohbet (Belge bazlı soru-cevap)
- [x] Seçili metin analizi (AI ile açıklama)

---

## ⏳ Devam Edenler ve Yapılacaklar

### AI Özellikleri - Aşama 3: Bilgi Yapılandırma (Altyapı Öncelikli)
- [x] **Zihin Haritası ve Bilgi Grafı Altyapısı**: Veri yapısının (JSON/Graph) oluşturulması ve LLM'den bu formatta çıktı alma (StructuringHandler)
- [ ] Zihin haritası görselleştirme (Kullanıcı yöntem belirlediğinde entegre edilecek)
- [x] Zaman çizelgesi (Timeline) çıkarımı (Özellikle raporlar ve tarihsel belgeler için)

### AI Özellikleri - Aşama 4: İş ve Profesyonel
- [x] Sözleşme analizi: Riskli maddelerin ve kritik yükümlülüklerin tespiti
- [x] Fatura / Belge veri çıkarımı: Tablo ve tutar extraction altyapısı
- [x] PDF Form otomatik doldurma asistanı (Tespit ve Öneri)

### Analiz ve Optimizasyon
- [x] Belge karşılaştırma (AI Diff): İki PDF arasındaki anlamsal farkların tespiti
- [x] Bias / Ton ve Okunabilirlik analizi (Metin seviyesi tespiti)
- [x] Metin Yeniden Yazma Geliştirmesi: Akademik dil, sadeleştirme ve farklı ton seçeneklerinin UI'a eklenmesi

### Gelişmiş Özellikler & Yayın
- [ ] Yerel model (Ollama) desteğinin tam entegrasyonu (Offline AI)
- [ ] Multimodal destek: PDF içindeki görsellerin ve diyagramların yorumlanması
- [ ] Kullanıcı alışkanlıklarına göre kişiselleştirme altyapısı
- [x] Performans iyileştirmeleri, log temizliği ve gizlilik odaklı optimizasyonlar
