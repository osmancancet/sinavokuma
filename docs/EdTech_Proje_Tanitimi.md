# PROJE TANITIM DOKÜMANI: Yapay Zeka Destekli Akademik Değerlendirme ve Sınav Otomasyonu Platformu

## 1. Yönetici Özeti ve İhtiyaç Analizi
Eğitim sektöründe, özellikle mühendislik fakülteleri ve meslek yüksekokullarında akademik personelin omuzlarındaki en büyük idari ve operasyonel yük, manuel sınav okuma süreçleridir. Bir akademisyenin vize ve final haftalarında yüzlerce öğrencinin açık uçlu, el yazısı ile doldurduğu sınav kağıtlarını değerlendirmesi; yüksek dikkat gerektiren, zaman alıcı ve tükenmişliğe yol açan bir süreçtir.

Bu proje, geleneksel optik form (test) okuyucularının ötesine geçerek; karmaşık el yazılarını, mühendislik formüllerini, tabloları ve çizimleri algılayabilen, okunan veriyi öğretmenin belirlediği rubrik (değerlendirme anahtarı) ile saniyeler içinde karşılaştırarak adil bir notlandırma önerisi sunan, **uçtan uca bir EdTech (Eğitim Teknolojileri) SaaS platformudur.**

## 2. Çözüm ve Temel Özellikler (Yapay Zeka & HTR)
Platform, geleneksel OCR (Optik Karakter Tanıma) yerine **HTR (Handwritten Text Recognition - El Yazısı Tanıma)** ve en gelişmiş Görsel Dil Modellerini (Vision-Language Models - Qwen2.5-VL, TrOCR vb.) kullanır.
*   **İnsanüstü Algılama:** Eğik, bitişik, silik veya kötü ışıkta yazılmış metinleri %95'in üzerinde doğrulukla dijital metne çevirir.
*   **Akıllı Rubrik Eşleştirme:** Öğretim görevlisi, sisteme "Soru 1: Değişken tanımlamaları 5 puan, döngü mantığı 10 puan, sözdizimi (syntax) hatasızlığı 5 puan" şeklinde bir rubrik girer. Yapay zeka, öğrencinin kağıdındaki kod bloğunu veya metni bu spesifik kriterlere göre analiz eder ve kısmi puanlamalar dahil olmak üzere detaylı bir gerekçe sunar.
*   **Adil ve Tarafsız Değerlendirme:** Yapay zeka yorgunluk, dikkat dağınıklığı veya önyargı (bias) barındırmadığı için tüm öğrencilere standart ve adil bir değerlendirme sunulur.

## 3. Çoklu Platform Yaklaşımı: Web ve Mobil Mimarisi
Proje, veri girişinin hızını ve değerlendirmenin detayını maksimize etmek için iki farklı platformda birbirine entegre çalışır:

### 3.1. Akademisyen Mobil Uygulaması (Veri Toplama ve Edge İşleme)
Mobil uygulama, akademisyenin amfide veya odasında kağıtları en hızlı şekilde sisteme aktarması için tasarlanmıştır.
*   **Akıllı Belge Tarayıcı (Document Scanner):** OpenCV altyapısı ile kağıdın 4 köşesi otomatik tespit edilir, perspektif yamuklukları düzeltilir (perspective warp) ve ortamdaki gölgeler temizlenerek "Edge Computing" (cihaz üzerinde işleme) ile dosya boyutu optimize edilir.
*   **Seri Çekim ve Çevrimdışı Mod:** İnternet bağlantısının zayıf olduğu kampüs ortamlarında kağıtlar cihaz önbelleğine kaydedilir, bağlantı sağlandığında arka planda sunucuya aktarılır.
*   **Tek Elle Kullanım (Ergonomi):** Yüzlerce kağıdın taranması sırasında ergonomi sağlamak amacıyla arayüz, tek elle hızlı çekim yapmaya uygun tasarlanmıştır.

### 3.2. Yönetim ve Değerlendirme Web Paneli (Dashboard)
Web paneli, bilgisayar başında detaylı inceleme, rubrik hazırlama ve raporlama işlemleri için kullanılır.
*   **Human-in-the-Loop (İnsan Onaylı Değerlendirme):** Sistem doğrudan notu transkripte işlemez. Web arayüzünde sol tarafta kağıdın orijinal fotoğrafı, sağ tarafta AI'nin okuduğu metin, verdiği puan ve gerekçesi sunulur. Akademisyen, tek tıkla bu notu onaylayabilir veya üzerinde manuel değişiklik yapabilir.
*   **Sürükle-Bırak Rubrik Oluşturucu:** Karmaşık sınavlar için farklı ağırlıklara sahip soru havuzları ve değerlendirme şablonları oluşturulabilir.
*   **Analitik ve Öğrenci Geri Bildirimi:** Sınav sonrasında sınıfın hangi konularda zorlandığını gösteren ısı haritaları (heatmaps) oluşturulur. Öğrencilere, hangi sorudan neden puan kırıldığını açıklayan detaylı, otomatik PDF geri bildirim raporları gönderilir.

## 4. Kurumsal Entegrasyon, Kalite ve Akreditasyon Süreçleri
Sistemin üniversiteler tarafından kabul görmesinin en büyük şartı, yasal mevzuatlara ve akreditasyon standartlarına uyumudur.

*   **MÜDEK, FEDEK ve YÖKAK Akreditasyonu (Kanıt Yönetimi):** Mühendislik ve teknik bilimler eğitiminde kalite güvencesi için ders kazanımlarının (outcomes) ölçülmesi zorunludur. Platform, her bir sınav sorusunu MÜDEK çıktılarıyla (örn: Çıktı 1: Karmaşık mühendislik problemlerini çözme becerisi) eşleştirir. Dönem sonunda denetçiler (auditors) için "Akreditasyon Kanıt Dosyası"nı otomatik olarak PDF şeklinde derler.
*   **YÖK / MEB Not Sistemi Entegrasyonu:** ÇGNO (4.0) hesabı, harf notu çan eğrisi adaptasyonları ve e-Okul / OBS (Öğrenci Bilgi Sistemi) API'leri ile çift yönlü veri akışı sağlanır.
*   **Kalite Güvence ve MLOps:** Yapay zeka modelleri düzenli olarak "ground truth" (insan tarafından doğrulanmış veri) ile test edilerek halüsinasyon oranları sıfıra yaklaştırılır.

## 5. Siber Güvenlik, KVKK ve Veri Yerelliği
*   **Veri Yerelliği (Data Residency):** Öğrenci sınav kağıtları ve not bilgileri 6698 sayılı KVKK kapsamında hassas veri statüsündedir. Platform, bulut altyapısını tamamen Türkiye sınırlarındaki veri merkezlerinde (Turkcell, Türk Telekom veya yerel sunucular) barındırır.
*   **Sıfır Güven (Zero Trust) Mimarisi:** Sistemdeki tüm API haberleşmeleri, veri tabanındaki dosyalar (at rest) ve ağ üzerindeki veriler (in transit) AES-256 standartlarında şifrelenir.
*   **Rol Bazlı Erişim (RBAC):** Sisteme giriş yapan bir araştırma görevlisi, akademisyen, bölüm başkanı ve akreditasyon denetçisinin erişim yetkileri kesin çizgilerle birbirinden ayrılır.

## 6. Sonuç
Bu platform, eğitim kurumlarındaki dijital dönüşümün en kritik eksik halkasını tamamlamaktadır. Akademisyenin idari yükünü hafifleterek araştırmaya ve eğitime daha fazla zaman ayırmasını sağlarken; öğrencilere anında, şeffaf ve adil geri bildirim vererek eğitim kalitesini artırır. Mobil ve Web'in entegre gücü, yapay zeka ile birleşerek modern eğitim kurumları için vazgeçilmez bir SaaS altyapısı sunmaktadır.
