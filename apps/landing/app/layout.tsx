import type { Metadata, Viewport } from "next";
import "./globals.css";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://rubrik.com.tr";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: "Rubrik — El yazısı sınav kağıtlarını okuyan yapay zekâ",
  description:
    "Açık uçlu sınav kağıtlarını okur, rubriğinize göre puanlar, her puanın gerekçesini yazar. " +
    "Notu siz onaylarsınız. MÜDEK, MEDEK, FEDEK ve YÖKAK kanıt dosyası Excel olarak otomatik hazırlanır. " +
    "Model kurumun kendi sunucusunda çalışır — KVKK uyumlu.",
  keywords: [
    "sınav okuma",
    "yapay zeka ile sınav değerlendirme",
    "MÜDEK",
    "MEDEK",
    "FEDEK",
    "YÖKAK",
    "akreditasyon",
    "program çıktısı",
    "kazanım analizi",
    "KVKK",
    "el yazısı tanıma",
  ],
  openGraph: {
    title: "Rubrik — Kağıtları okumayı bize bırakın. Son sözü siz söyleyin.",
    description:
      "El yazısını okur, rubriğinize göre puanlar, gerekçesini yazar. " +
      "Notu transkripte işleyen tek kişi hâlâ sizsiniz.",
    locale: "tr_TR",
    type: "website",
  },
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#EAEDF3" },
    { media: "(prefers-color-scheme: dark)", color: "#0C1122" },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="tr">
      <body>{children}</body>
    </html>
  );
}
