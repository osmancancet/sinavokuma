"use client";

import { useCallback, useRef, useState } from "react";

/*
  Kağıt görüntüleyici — zoom + pan (SRS §3.2 "resim zoom yapılabilir").
  El yazısını okumak için akademisyenin yakınlaşması şart. Tekerlek = zoom,
  sürükle = pan, çift tık = sıfırla.

  Görsel MinIO'dan imzalı URL ile gelir (KVKK — bucket public değil).
*/

export default function PaperViewer({ src, studentNo }: { src: string; studentNo: string }) {
  const [scale, setScale] = useState(1);
  const [pos, setPos] = useState({ x: 0, y: 0 });
  const [dragging, setDragging] = useState(false);
  const [failed, setFailed] = useState(false);
  const dragStart = useRef({ x: 0, y: 0, px: 0, py: 0 });

  const onWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    setScale((s) => Math.min(Math.max(s - e.deltaY * 0.0015, 0.5), 5));
  }, []);

  const onDown = (e: React.MouseEvent) => {
    setDragging(true);
    dragStart.current = { x: e.clientX, y: e.clientY, px: pos.x, py: pos.y };
  };
  const onMove = (e: React.MouseEvent) => {
    if (!dragging) return;
    setPos({
      x: dragStart.current.px + (e.clientX - dragStart.current.x),
      y: dragStart.current.py + (e.clientY - dragStart.current.y),
    });
  };
  const stop = () => setDragging(false);
  const reset = () => {
    setScale(1);
    setPos({ x: 0, y: 0 });
  };

  return (
    <div className="viewer">
      <div className="viewer-toolbar">
        <span className="mono viewer-no">{studentNo}</span>
        <div className="viewer-zoom">
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={() => setScale((s) => Math.max(s - 0.25, 0.5))}
            aria-label="Uzaklaş"
          >
            −
          </button>
          <span className="mono viewer-scale">{Math.round(scale * 100)}%</span>
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={() => setScale((s) => Math.min(s + 0.25, 5))}
            aria-label="Yakınlaş"
          >
            +
          </button>
          <button type="button" className="btn btn-ghost btn-sm" onClick={reset}>
            Sıfırla
          </button>
        </div>
      </div>

      <div
        className="viewer-canvas"
        onWheel={onWheel}
        onMouseDown={onDown}
        onMouseMove={onMove}
        onMouseUp={stop}
        onMouseLeave={stop}
        onDoubleClick={reset}
        style={{ cursor: dragging ? "grabbing" : "grab" }}
      >
        {failed ? (
          <div className="state" style={{ color: "var(--ink-3)" }}>
            <p>Kağıt görseli yüklenemedi.</p>
            <p style={{ fontSize: ".8rem" }}>İmzalı bağlantının süresi dolmuş olabilir.</p>
          </div>
        ) : (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={src}
            alt={`${studentNo} numaralı öğrencinin sınav kağıdı`}
            draggable={false}
            onError={() => setFailed(true)}
            style={{
              transform: `translate(${pos.x}px, ${pos.y}px) scale(${scale})`,
              transformOrigin: "center center",
              transition: dragging ? "none" : "transform .08s",
            }}
          />
        )}
      </div>

      <style>{`
        .viewer { height: 100%; display: flex; flex-direction: column; }
        .viewer-toolbar {
          display: flex; align-items: center; justify-content: space-between; gap: 1rem;
          padding: .5rem .8rem; border-bottom: 1px solid var(--hairline); background: var(--surface);
        }
        .viewer-no { font-size: .82rem; font-weight: 650; color: var(--ink-2); }
        .viewer-zoom { display: flex; align-items: center; gap: .35rem; }
        .viewer-scale { font-size: .78rem; color: var(--ink-3); min-width: 3rem; text-align: center; }
        .viewer-canvas {
          flex: 1; overflow: hidden; display: grid; place-items: center;
          user-select: none; position: relative;
        }
        .viewer-canvas img { max-width: 95%; max-height: 95%; box-shadow: 0 8px 30px -12px rgba(22,34,74,.5); border-radius: 2px; }
      `}</style>
    </div>
  );
}
