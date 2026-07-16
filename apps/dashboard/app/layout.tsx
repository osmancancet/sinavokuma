import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Rubrik — Değerlendirme Paneli",
  description: "Sınav kağıtlarını değerlendirme ve akreditasyon paneli.",
  robots: { index: false, follow: false },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#EAEDF3" },
    { media: "(prefers-color-scheme: dark)", color: "#0C1122" },
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="tr">
      <body>{children}</body>
    </html>
  );
}
