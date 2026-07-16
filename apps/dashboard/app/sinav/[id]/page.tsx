"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";

import { listPapers, type Paper } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import TopBar from "../../TopBar";

const STATUS = {
  PENDING: { cls: "badge-pending", text: "Bekliyor" },
  AI_SCORED: { cls: "badge-scored", text: "AI okudu" },
  APPROVED: { cls: "badge-approved", text: "Onaylandı" },
  FAILED: { cls: "badge-failed", text: "Hata" },
} as const;

export default function ExamPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const examId = Number(id);
  const { user, loading, logout } = useAuth();
  const [papers, setPapers] = useState<Paper[]>([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    listPapers(examId)
      .then(setPapers)
      .catch((e) => setError(e.message))
      .finally(() => setDataLoading(false));
  }, [user, examId]);

  if (loading || !user) {
    return (
      <div className="state">
        <div className="spinner" />
      </div>
    );
  }

  const counts = papers.reduce(
    (acc, p) => {
      acc[p.status] = (acc[p.status] ?? 0) + 1;
      return acc;
    },
    {} as Record<Paper["status"], number>,
  );
  const approved = counts.APPROVED ?? 0;
  const total = papers.length;

  // İlk değerlendirilmemiş kağıt — "Değerlendirmeye başla" onu açar.
  const firstReviewable = papers.find((p) => p.status === "AI_SCORED" || p.status === "APPROVED");

  return (
    <>
      <TopBar user={user} onLogout={logout} />
      <div className="container">
        <div className="breadcrumb">
          <Link href="/">Derslerim</Link> <span>/</span> <span>Sınav</span>
        </div>

        <div
          className="page-head"
          style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", gap: "1rem", flexWrap: "wrap" }}
        >
          <div>
            <h1>Sınav Kağıtları</h1>
            <p className="sub">
              {total} kağıt · {approved} onaylandı
              {counts.AI_SCORED ? ` · ${counts.AI_SCORED} değerlendirme bekliyor` : ""}
            </p>
          </div>
          <div style={{ display: "flex", gap: ".6rem" }}>
            {firstReviewable && (
              <Link href={`/degerlendir/${firstReviewable.id}`} className="btn btn-primary">
                Değerlendirmeye başla
              </Link>
            )}
            <Link href={`/sinav/${examId}/rapor`} className="btn btn-ghost">
              Akreditasyon raporu
            </Link>
          </div>
        </div>

        {error && <div className="error-box">{error}</div>}

        {dataLoading ? (
          <div className="state">
            <div className="spinner" />
          </div>
        ) : total === 0 ? (
          <div className="state">
            <h3>Henüz kağıt yok</h3>
            <p>Bu sınava mobil uygulamadan kağıt yüklendiğinde burada görünür.</p>
          </div>
        ) : (
          <div className="card">
            <div className="list">
              {papers.map((p) => {
                const s = STATUS[p.status];
                const clickable = p.status === "AI_SCORED" || p.status === "APPROVED";
                const inner = (
                  <>
                    <div>
                      <div className="title mono">{p.student_no}</div>
                      {p.status === "FAILED" && p.error_message && (
                        <div className="sub" style={{ color: "var(--red)" }}>
                          {p.error_message}
                        </div>
                      )}
                    </div>
                    <span className={`badge ${s.cls}`}>{s.text}</span>
                    <span style={{ color: "var(--ink-3)" }}>{clickable ? "→" : ""}</span>
                  </>
                );
                return clickable ? (
                  <Link
                    key={p.id}
                    href={`/degerlendir/${p.id}`}
                    className="list-row"
                    style={{ gridTemplateColumns: "1fr auto 1.5rem" }}
                  >
                    {inner}
                  </Link>
                ) : (
                  <div
                    key={p.id}
                    className="list-row"
                    style={{ gridTemplateColumns: "1fr auto 1.5rem", cursor: "default" }}
                  >
                    {inner}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </>
  );
}
