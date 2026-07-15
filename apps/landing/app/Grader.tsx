"use client";

import { useEffect, useRef, useState } from "react";

/*
  Ürünün değerlendirme ekranı, hero'nun içinde canlı olarak çalışıyor.
  Sıra ürünün tezini anlatıyor: tara → makine okur → makine puanlar → İNSAN onaylar.
  Kırmızı yalnızca son adımda beliriyor.
*/

const OKUNAN = `int toplam = 0;
for (int i = 1; i <= n; i++) {
    toplam = toplam + i
}
printf("%d", toplam);`;

type Criterion = {
  name: string;
  why: string;
  given: number;
  max: number;
  partial?: boolean;
};

const CRITERIA: Criterion[] = [
  {
    name: "Değişken tanımlamaları",
    why: "toplam doğru tipte ve sıfıra ilklendirilmiş.",
    given: 5,
    max: 5,
  },
  {
    name: "Döngü mantığı",
    why: "1'den n'e kadar doğru toplama; sınır koşulu (i <= n) doğru.",
    given: 10,
    max: 10,
  },
  {
    name: "Sözdizimi hatasızlığı",
    why: "Döngü içindeki atamada noktalı virgül eksik. Mantık doğru, kısmi puan.",
    given: 3,
    max: 5,
    partial: true,
  },
];

const TOTAL = CRITERIA.reduce((sum, c) => sum + c.given, 0); // 18
const MAX = CRITERIA.reduce((sum, c) => sum + c.max, 0); // 20

export default function Grader() {
  const rootRef = useRef<HTMLDivElement>(null);
  const [scanning, setScanning] = useState(false);
  const [typed, setTyped] = useState("");
  const [typingDone, setTypingDone] = useState(false);
  const [shown, setShown] = useState(0);
  const [score, setScore] = useState(0);
  const [ready, setReady] = useState(false);
  const [approved, setApproved] = useState(false);

  useEffect(() => {
    const node = rootRef.current;
    if (!node) return;

    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) {
      setTyped(OKUNAN);
      setTypingDone(true);
      setShown(CRITERIA.length);
      setScore(TOTAL);
      return;
    }

    const timers: ReturnType<typeof setTimeout>[] = [];

    const start = () => {
      setScanning(true);

      timers.push(
        setTimeout(() => {
          let i = 0;
          const type = () => {
            i += 2;
            setTyped(OKUNAN.slice(0, i));
            if (i <= OKUNAN.length) {
              timers.push(setTimeout(type, 16));
            } else {
              setTypingDone(true);
              CRITERIA.forEach((_, idx) => {
                timers.push(setTimeout(() => setShown(idx + 1), idx * 420));
              });
              timers.push(
                setTimeout(() => {
                  let n = 0;
                  const count = () => {
                    setScore(n);
                    if (n < TOTAL) {
                      n += 1;
                      timers.push(setTimeout(count, 45));
                    } else {
                      setReady(true);
                    }
                  };
                  count();
                }, CRITERIA.length * 420 + 150),
              );
            }
          };
          type();
        }, 1400),
      );
    };

    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            io.disconnect();
            start();
          }
        });
      },
      { threshold: 0.25 },
    );
    io.observe(node);

    return () => {
      io.disconnect();
      timers.forEach(clearTimeout);
    };
  }, []);

  return (
    <div className="grader" ref={rootRef}>
      <div className="grader-bar">
        <span>
          <b>BMG101</b> — Programlamaya Giriş · Vize Sınavı
        </span>
        <span className="paper-count">Kağıt 47 / 312</span>
      </div>

      <div className="grader-body">
        {/* Sol: taranmış kağıt */}
        <div className={`scan${scanning ? " scanning" : ""}`}>
          <div className="sheet">
            <div className="scanline" />
            <div className="sheet-head">Öğrenci No: 20210777</div>
            <pre className="sheet-code">{`Soru 1:

int toplam = 0;
for (int i = 1; i <= n; i++) {
    toplam = toplam + i
}
printf("%d", toplam);`}</pre>
          </div>
        </div>

        {/* Sağ: makinenin okuması, sonra insanın kararı */}
        <div className="verdict">
          <div>
            <div className="block-label">
              <span className="dot machine" /> Yapay zekânın okuduğu
            </div>
            <div className="transcript">
              {typed}
              {!typingDone && <span className="caret" />}
            </div>
          </div>

          <div>
            <div className="block-label">
              <span className="dot machine" /> Rubriğinize göre
            </div>
            <div className="rubric">
              {CRITERIA.map((c, i) => (
                <div
                  key={c.name}
                  className={`crit${c.partial ? " partial" : ""}${i < shown ? " in" : ""}`}
                >
                  <span className="tick">{c.partial ? "±" : "✓"}</span>
                  <span className="name">
                    {c.name}
                    <small className="why">{c.why}</small>
                  </span>
                  <span className="pts">
                    {c.given} / {c.max}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="score-row">
            <div className="score">
              {score}
              <small> / {MAX}</small>
            </div>
            <div className="score-label">
              Yapay zekânın <b>önerisi</b>. Onaylayana kadar hiçbir yere işlenmez.
            </div>
          </div>

          <div className="actions">
            <button
              type="button"
              className={`btn btn-primary${ready && !approved ? " ready" : ""}`}
              style={approved ? { background: "var(--green)" } : undefined}
              onClick={() => setApproved(true)}
            >
              {approved ? "✓ Onaylandı — not kaydedildi" : "✓ Onayla ve sonraki kağıt"}
            </button>
            <button type="button" className="btn btn-ghost">
              Puanı düzelt
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
