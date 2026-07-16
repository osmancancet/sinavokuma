"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import {
  approvePaper,
  getReview,
  listPapers,
  listQuestions,
  type Question,
  type ReviewScreen,
} from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import TopBar from "../../TopBar";
import PaperViewer from "./PaperViewer";

/*
  SRS GÖREV 8 — Değerlendirme ekranı. Ürünün kalbi.
  Sol: kağıdın aslı (zoom + pan). Sağ: AI'ın okuduğu metin, rubrik kırılımı,
  önerdiği puan, gerekçesi. Hoca tek tuşla onaylar veya puanı düzeltir.

  Klavye kısayolları bilinçli: bir akademisyen yüzlerce kağıt arasında dolaşırken
  fareye uzanmak yavaşlatır. Enter = onayla + sonraki.
*/

export default function EvaluatePage({ params }: { params: Promise<{ paperId: string }> }) {
  const { paperId } = use(params);
  const pid = Number(paperId);
  const router = useRouter();
  const { user, loading, logout } = useAuth();

  const [review, setReview] = useState<ReviewScreen | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [edited, setEdited] = useState<Record<number, number>>({}); // score_id -> düzeltilmiş puan
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [nextId, setNextId] = useState<number | null>(null);
  const [examId, setExamId] = useState<number | null>(null);

  // Değerlendirme ekranı verisini yükle.
  useEffect(() => {
    if (!user) return;
    let alive = true;
    (async () => {
      try {
        const r = await getReview(pid);
        if (!alive) return;
        setReview(r);
        setEdited({});
        setExamId(r.exam_id);
        // Rubrik + max puan için soruları, sonraki kağıt için listeyi çek.
        const [qs, papers] = await Promise.all([
          listQuestions(r.exam_id),
          listPapers(r.exam_id),
        ]);
        if (!alive) return;
        setQuestions(qs);
        const idx = papers.findIndex((p) => p.id === pid);
        const next = papers
          .slice(idx + 1)
          .find((p) => p.status === "AI_SCORED" || p.status === "APPROVED");
        setNextId(next?.id ?? null);
      } catch (e) {
        if (alive) setError(e instanceof Error ? e.message : "Yüklenemedi.");
      }
    })();
    return () => {
      alive = false;
    };
  }, [pid, user]);

  const questionById = new Map(questions.map((q) => [q.id, q]));

  function currentFinal(scoreId: number, aiScore: number | null): number {
    if (scoreId in edited) return edited[scoreId];
    return aiScore ?? 0;
  }

  async function handleApprove() {
    if (!review) return;
    setBusy(true);
    setError(null);
    try {
      const decisions = review.scores.map((s) => ({
        score_id: s.id,
        final_score: currentFinal(s.id, s.ai_score),
      }));
      await approvePaper(pid, decisions);
      if (nextId) {
        router.push(`/degerlendir/${nextId}`);
      } else if (examId) {
        router.push(`/sinav/${examId}`);
      } else {
        router.push("/");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Onaylanamadı.");
      setBusy(false);
    }
  }

  // Klavye: Enter = onayla + sonraki
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA") return;
      if (e.key === "Enter" && !busy) {
        e.preventDefault();
        handleApprove();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [busy, review, edited, nextId, examId]);

  if (loading || !user) {
    return (
      <div className="state">
        <div className="spinner" />
      </div>
    );
  }

  const total = review
    ? review.scores.reduce((sum, s) => sum + currentFinal(s.id, s.ai_score), 0)
    : 0;
  const maxTotal = questions.reduce((sum, q) => sum + Number(q.max_score), 0);
  const anyEdited = Object.keys(edited).length > 0;

  return (
    <>
      <TopBar user={user} onLogout={logout} />

      <div className="eval-bar">
        <Link href={examId ? `/sinav/${examId}` : "/"} className="btn btn-ghost btn-sm">
          ← Listeye dön
        </Link>
        {review && (
          <div className="eval-bar-info">
            <span className="mono" style={{ fontWeight: 650 }}>
              {review.student_no}
            </span>
            {review.status === "APPROVED" && (
              <span className="badge badge-approved">Onaylandı</span>
            )}
          </div>
        )}
        <div style={{ display: "flex", gap: ".5rem", alignItems: "center" }}>
          <kbd className="kbd">Enter</kbd>
          <span style={{ fontSize: ".8rem", color: "var(--ink-3)" }}>onayla + sonraki</span>
        </div>
      </div>

      {error && (
        <div className="container" style={{ margin: "1rem auto" }}>
          <div className="error-box">{error}</div>
        </div>
      )}

      {!review ? (
        <div className="state">
          <div className="spinner" />
        </div>
      ) : (
        <div className="eval-split">
          {/* SOL: kağıdın aslı */}
          <div className="eval-left">
            <PaperViewer src={review.image_url} studentNo={review.student_no} />
          </div>

          {/* SAĞ: makinenin okuması + insanın kararı */}
          <div className="eval-right">
            {review.scores.map((s) => {
              const q = questionById.get(s.question_id);
              const maxScore = q ? Number(q.max_score) : null;
              const final = currentFinal(s.id, s.ai_score);
              return (
                <div key={s.id} className="q-block">
                  <div className="q-head">
                    <h3>{q ? `Soru ${q.question_number}` : `Soru #${s.question_id}`}</h3>
                    {maxScore != null && (
                      <span className="q-max">tam puan {maxScore}</span>
                    )}
                  </div>

                  {q?.prompt && <p className="q-prompt">{q.prompt}</p>}

                  <div className="block-label">
                    <span className="dot machine" /> Yapay zekânın okuduğu
                  </div>
                  <pre className="transcript">{s.ai_raw_text ?? "(okunamadı)"}</pre>

                  {q?.rubric_criteria && q.rubric_criteria.length > 0 && (
                    <>
                      <div className="block-label">
                        <span className="dot machine" /> Rubrik
                      </div>
                      <ul className="rubric">
                        {q.rubric_criteria.map((c, i) => (
                          <li key={i}>
                            <span>{c.kriter}</span>
                            <span className="mono">{c.puan} p</span>
                          </li>
                        ))}
                      </ul>
                    </>
                  )}

                  {s.ai_reasoning && (
                    <details className="reasoning">
                      <summary>AI gerekçesi</summary>
                      <pre>{s.ai_reasoning}</pre>
                    </details>
                  )}

                  <div className="score-line">
                    <div className="ai-suggest">
                      <span className="lbl">AI önerisi</span>
                      <span className="mono val">{s.ai_score ?? "—"}</span>
                    </div>
                    <div className="arrow">→</div>
                    <div className="final-input">
                      <span className="lbl">Sizin notunuz</span>
                      <input
                        className="mono"
                        type="number"
                        min={0}
                        max={maxScore ?? undefined}
                        step="0.5"
                        value={final}
                        onChange={(e) => {
                          const v = e.target.value === "" ? 0 : Number(e.target.value);
                          const clamped =
                            maxScore != null ? Math.min(Math.max(v, 0), maxScore) : Math.max(v, 0);
                          setEdited((prev) => ({ ...prev, [s.id]: clamped }));
                        }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}

            <div className="eval-footer">
              <div className="total">
                <span className="lbl">Toplam</span>
                <span className="total-val mono">
                  {total}
                  {maxTotal > 0 && <small> / {maxTotal}</small>}
                </span>
              </div>
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleApprove}
                disabled={busy}
              >
                {busy
                  ? "Kaydediliyor…"
                  : anyEdited
                    ? "Düzeltilmiş notu onayla"
                    : review.status === "APPROVED"
                      ? "Yeniden onayla"
                      : "Onayla ve sonraki"}
              </button>
            </div>
          </div>
        </div>
      )}

      <style>{`
        .eval-bar {
          display: flex; align-items: center; justify-content: space-between; gap: 1rem;
          padding: .6rem 1.5rem; background: var(--surface); border-bottom: 1px solid var(--hairline);
          position: sticky; top: 58px; z-index: 15;
        }
        .eval-bar-info { display: flex; align-items: center; gap: .6rem; }
        .kbd {
          font-family: var(--mono); font-size: .72rem; padding: .12rem .4rem;
          border: 1px solid var(--hairline); border-bottom-width: 2px; border-radius: 4px;
          background: var(--surface-2);
        }
        .eval-split { display: grid; grid-template-columns: 1fr 1fr; height: calc(100dvh - 58px - 49px); }
        @media (max-width: 900px) { .eval-split { grid-template-columns: 1fr; height: auto; } }
        .eval-left { border-right: 1px solid var(--hairline); background: var(--surface-2); overflow: hidden; }
        @media (max-width: 900px) { .eval-left { height: 60dvh; border-right: 0; border-bottom: 1px solid var(--hairline); } }
        .eval-right { overflow-y: auto; padding: 1.5rem; display: flex; flex-direction: column; gap: 1.5rem; }

        .q-block { border-bottom: 1px solid var(--hairline); padding-bottom: 1.3rem; }
        .q-block:last-of-type { border-bottom: 0; }
        .q-head { display: flex; align-items: baseline; justify-content: space-between; }
        .q-head h3 { font-size: 1.15rem; }
        .q-max { font-size: .8rem; color: var(--ink-3); }
        .q-prompt { font-size: .88rem; color: var(--ink-2); margin: .4rem 0 .8rem; }

        .block-label {
          display: flex; align-items: center; gap: .45rem; margin: .9rem 0 .4rem;
          font-size: .68rem; font-weight: 650; letter-spacing: .1em; text-transform: uppercase; color: var(--ink-3);
        }
        .dot { width: 6px; height: 6px; border-radius: 50%; }
        .dot.machine { background: var(--blue); }
        .transcript {
          font-family: var(--mono); font-size: .82rem; line-height: 1.6; white-space: pre-wrap;
          background: var(--surface-2); border: 1px solid var(--hairline); border-left: 2px solid var(--blue);
          border-radius: var(--radius); padding: .7rem .8rem; margin: 0; color: var(--ink);
        }
        .rubric { list-style: none; margin: 0; padding: 0; }
        .rubric li {
          display: flex; justify-content: space-between; gap: 1rem;
          padding: .35rem 0; border-bottom: 1px dashed var(--hairline); font-size: .88rem;
        }
        .rubric li:last-child { border-bottom: 0; }
        .rubric .mono { color: var(--ink-2); }
        .reasoning { margin-top: .8rem; }
        .reasoning summary { font-size: .82rem; color: var(--blue); cursor: pointer; }
        .reasoning pre {
          font-family: var(--sans); font-size: .84rem; line-height: 1.55; white-space: pre-wrap;
          color: var(--ink-2); margin: .5rem 0 0; padding: .7rem .8rem;
          background: var(--surface-2); border-radius: var(--radius);
        }

        .score-line { display: flex; align-items: flex-end; gap: 1rem; margin-top: 1.1rem; }
        .score-line .lbl { display: block; font-size: .7rem; letter-spacing: .05em; text-transform: uppercase; color: var(--ink-3); margin-bottom: .3rem; }
        .ai-suggest .val { font-size: 1.5rem; color: var(--ink-2); }
        .score-line .arrow { color: var(--ink-3); padding-bottom: .3rem; }
        .final-input input {
          width: 6rem; font-size: 1.5rem; padding: .3rem .5rem; text-align: right;
          border: 1px solid var(--red); border-radius: var(--radius);
          background: var(--surface); color: var(--red); font-weight: 600;
        }
        .final-input input:focus { outline: 2px solid var(--red); outline-offset: 1px; }

        .eval-footer {
          position: sticky; bottom: 0; margin: 0 -1.5rem -1.5rem; padding: 1rem 1.5rem;
          background: var(--surface); border-top: 1px solid var(--hairline);
          display: flex; align-items: center; justify-content: space-between; gap: 1rem;
        }
        .total .lbl { display: block; font-size: .7rem; text-transform: uppercase; letter-spacing: .05em; color: var(--ink-3); }
        .total-val { font-family: var(--serif); font-size: 2rem; color: var(--red); line-height: 1; }
        .total-val small { font-size: 1rem; color: var(--ink-3); }
      `}</style>
    </>
  );
}
