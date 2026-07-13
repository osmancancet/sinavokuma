# KAPSAMLI GELİŞTİRME VE YAZILIM MİMARİ REHBERİ (SRS)

Bu doküman, "Yapay Zeka Destekli Sınav Otomasyonu" projesinin hem Web hem Mobil bacaklarını kapsayan, Claude/LLM gibi yapay zeka asistanları ile kodlama yaparken kullanılacak **Sistem Gereksinimleri ve Geliştirme Adımları** rehberidir. Mimarideki temel amaç; yüksek erişilebilirlik, siber güvenlik önlemleri, MÜDEK uyumluluğu ve asenkron (kuyruk tabanlı) yapay zeka işlemidir.

---

## 1. SİSTEM MİMARİSİ VE TEKNOLOJİ YIĞINI

### 1.1. Frontend - Mobil (Veri Toplama Katmanı)
*   **Framework:** React Native (TypeScript).
*   **Görüntü İşleme:** `react-native-vision-camera` ve JSI (JavaScript Interface) üzerinden doğrudan OpenCV C++ binding'leri. (Performans için köprü(bridge) kullanılmayacak).
*   **State Management:** Zustand veya Redux Toolkit.
*   **Network/Offline:** TanStack Query (React Query) ve MMKV (çok hızlı lokal depolama). İnternet yokken kağıtlar MMKV'de tutulur, bağlantı gelince arka planda aktarılır.

### 1.2. Frontend - Web (Yönetim ve Onay Katmanı)
*   **Framework:** Next.js (App Router, TypeScript).
*   **UI/UX:** Tailwind CSS ve shadcn/ui (akademik, temiz, profesyonel kurumsal arayüz).
*   **PDF/Raporlama:** `react-pdf` (MÜDEK kanıt dosyaları ve öğrenci geri bildirim karneleri oluşturmak için).

### 1.3. Backend - Mikroservisler (Koordinasyon ve Veri Katmanı)
*   **API Gateway & Core API:** Node.js (NestJS) veya Python (FastAPI). Sıkı tip denetimi ve Swagger/OpenAPI desteği için FastAPI tercih edilebilir.
*   **Veritabanı:** PostgreSQL (Relational Data) ve Prisma ORM (veya SQLAlchemy).
*   **Message Broker (Kuyruk):** RabbitMQ. Yüzlerce fotoğraf aynı anda yüklendiğinde AI sunucusunun çökmemesi için istekler sıraya dizilir.
*   **Dosya Depolama:** MinIO (AWS S3 uyumlu). Görseller S3 bucket'larında tutulur.

### 1.4. AI / Inference Servisi (İşlem Katmanı)
*   **Framework:** Python, PyTorch, FastAPI (Sadece GPU sunucusunda çalışır, dışarıya kapalıdır).
*   **Orkestrasyon:** LangChain veya LlamaIndex (Metni alıp rubrik ile işlemek için).
*   **Modeller:** Qwen2.5-VL / TrOCR (Görsel okuma), GPT-4o-mini veya Llama-3 (Rubrik analizi ve notlandırma).

---

## 2. VERİTABANI TASARIMI (CORE SCHEMA)

Aşağıdaki şema, Claude'a PostgreSQL ORM modellerini (Prisma/SQLAlchemy) yazdırmak için kullanılacaktır.

*   **Users:** `id`, `email`, `password_hash`, `role` (ADMIN, TEACHER, AUDITOR), `created_at`
*   **Courses:** `id`, `code` (örn: BMG101), `name`, `department_id`, `teacher_id`
*   **Mudek_Outcomes (MÜDEK Çıktıları):** `id`, `course_id`, `outcome_code` (örn: Ç1, Ç2), `description`
*   **Exams:** `id`, `course_id`, `title`, `date`, `total_score`, `status` (DRAFT, PROCESSING, COMPLETED)
*   **Questions:** `id`, `exam_id`, `question_number`, `max_score`, `mudek_outcome_id`, `expected_answer` (Metin), `rubric_criteria` (JSON)
*   **Student_Papers:** `id`, `exam_id`, `student_no`, `image_url` (S3 path), `status` (PENDING, AI_SCORED, APPROVED)
*   **Paper_Scores:** `id`, `student_paper_id`, `question_id`, `ai_raw_text` (okunan metin), `ai_score`, `ai_reasoning` (neden bu notu verdi), `final_score` (Hoca müdahale ederse değişen not).

---

## 3. ADIM ADIM GELİŞTİRME FAZLARI (CLAUDE'A VERİLECEK GÖREVLER)

Bu dokümanı LLM'e (Claude'a) bağlam (context) olarak verip, aşağıdaki fazları sırasıyla talep edin:

### FAZ 1: Backend Altyapısı ve Siber Güvenlik (Zero Trust)
*   **GÖREV 1:** "SRS dokümanını referans alarak, PostgreSQL ve FastAPI kullanarak veritabanı şemasını (Modelleri) oluştur."
*   **GÖREV 2:** "JWT tabanlı, Role-Based Access Control (RBAC) içeren kimlik doğrulama sistemini yaz. Güvenlik için bcrypt şifrelemesi ve yetkilendirme middleware'i ekle."
*   **GÖREV 3:** "MinIO (S3) entegrasyonunu yap. Mobil uygulamanın güvenli şekilde dosya yükleyebilmesi için 'Presigned URL' üreten endpoint'i yaz."

### FAZ 2: AI / Inference Mimarisi ve Kuyruk Sistemi
*   **GÖREV 4:** "RabbitMQ entegrasyonunu kur. API'ye bir sınav kağıdı kaydı düştüğünde, işlemi `paper_processing_queue` isimli kuyruğa gönderen yapıyı yaz."
*   **GÖREV 5:** "Ayrı bir Python FastAPI servisi (Inference Worker) yaz. Bu servis RabbitMQ'yu dinlesin. Gelen S3 görsel linkini indirsin, Qwen-VL modelini taklit eden (mock) bir fonksiyonla metne çevirsin."
*   **GÖREV 6:** "Okunan metni `Questions` tablosundaki rubrik ve beklenen cevap ile karşılaştırıp puan veren LangChain tabanlı bir Prompt Template yaz. Sonucu `Paper_Scores` tablosuna kaydet."

### FAZ 3: Web Dashboard (Human-in-the-loop & MÜDEK)
*   **GÖREV 7:** "Next.js ve Tailwind CSS kullanarak, bir akademisyenin giriş yapıp derslerini ve sınavlarını görebileceği Dashboard arayüzünü oluştur."
*   **GÖREV 8:** "Sınav Değerlendirme Ekranını tasarla. Ekran ikiye bölünmüş olmalı; solda sınav kağıdı resmi (zoom yapılabilir), sağda AI'nin çıkardığı metin, rubrik tablosu, önerdiği not ve onaylama (Approve/Edit) butonları olsun."
*   **GÖREV 9 (Akreditasyon):** "Sınav onaylandıktan sonra, soruların bağlı olduğu `mudek_outcome_id`'leri baz alarak, sınıfın genel MÜDEK başarı oranını hesaplayan SQL sorgusunu ve bunu Web'de grafiksel gösteren bileşeni (Chart.js/Recharts) yaz."

### FAZ 4: Mobil Uygulama (Görüntü İşleme ve Edge)
*   **GÖREV 10:** "React Native ile bir kamera ekranı oluştur. Kullanıcı fotoğraf çektiğinde, cihazın çevrimdışı (offline) olma ihtimaline karşı MMKV'ye kaydeden bir yapı kur."
*   **GÖREV 11:** "TanStack Query'nin offline mutation özelliğini kullanarak, internet bağlantısı sağlandığında MMKV'deki fotoğrafları FAZ 1'de yazdığımız Presigned URL endpoint'ine upload eden arka plan senkronizasyon (background sync) servisini yaz."

---

## 4. GELİŞTİRİCİ NOTLARI VE OPTİMİZASYON
*   **Prompting (İstem Mühendisliği):** Yapay zekaya rubrik verirken "Chain of Thought" (Düşünce Zinciri) tekniği kullanılmalıdır. Sisteme "Önce öğrencinin kodunu analiz et, sonra rubrikteki 1. şarta uyup uymadığını yaz, sonra 2. şarta bak ve en son notu ver" şeklinde direktif verilmesi başarı oranını %90'lardan %98'lere çıkarır.
*   **CORS ve Rate Limiting:** Akademik verilerin korunması (DDoS vb. saldırılara karşı) için API Gateway üzerinde katı bir Rate Limiting (IP bazlı hız sınırı) uygulanmalıdır.
*   **CI/CD:** GitHub Actions üzerinden kodlar her push edildiğinde, otomatik Pytest senaryoları çalıştırılmalı, AI modellerinin test verilerindeki doğruluğu (accuracy) onaylanmadan canlı ortama (production) geçilmemelidir.
