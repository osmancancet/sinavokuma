# Rubrik — Tanıtım Sitesi

Yapay zeka destekli sınav okuma platformunun herkese açık tanıtım sayfası.
Next.js 16 (App Router) · statik export · öğrenci verisi içermez.

## Yerel çalıştırma
```bash
npm install
npm run dev      # http://localhost:3000
```

## Vercel'e deploy
Bu klasör (`apps/landing`) bağımsız bir Next.js projesidir. Monorepo içinde
olduğu için Vercel'de **Root Directory** ayarını `apps/landing` yapın:

1. vercel.com → Add New → Project → repoyu içe aktar
2. Root Directory: `apps/landing`
3. Framework: Next.js (otomatik algılanır)
4. Deploy

Özel alan adı: Vercel → Project → Settings → Domains → alan adınızı ekleyin,
DNS'te verilen kaydı (A veya CNAME) tanımlayın.

Not: Bu site KVKK açısından güvenlidir çünkü hiçbir öğrenci verisi işlemez.
Değerlendirme paneli (öğrenci kağıtları) kurumun KENDİ sunucusunda çalışır,
Vercel'de değil.
