"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";

import {
  downloadExcel,
  getAccreditation,
  type AccreditationReport,
  type Attainment,
} from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import TopBar from "../../../TopBar";

/*
  SRS GÖREV 9 — MÜDEK/MEDEK analitik. Yalnızca onaylanmış notlardan hesaplanır.
  Üstte program çıktıları (PÇ — denetçinin baktığı), altta ders çıktıları (DÇ).
  İki Excel: OBS not listesi + denetçi kanıt dosyası.
*/

export default function ReportPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const examId = Number(id);
  const { user, loading, logout } = useAuth();
  const [threshold, setThreshold] = useState(50);
  const [report, setReport] = useState<AccreditationReport | null>(null);
  const [dataLoading, setDataLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    setDataLoading(true);
    getAccreditation(examId, threshold)
      .then(setReport)
      .catch((e) => setError(e.message))
      .finally(() => setDataLoading(false));
  }, [user, examId, threshold]);

  async function download(kind: "grades" | "accreditation") {
    setDownloading(kind);
    try {
      const path =
        kind === "grades"
          ? `/api/v1/exams/${examId}/grades.xlsx`
          : `/api/v1/exams/${examId}/accreditation.xlsx?threshold=${threshold}`;
      const name = kind === "grades" ? "obs_not_listesi.xlsx" : "kazanim_raporu.xlsx";
      await downloadExcel(path, name);
    } catch (e) {
      setError(e instanceof Error ? e.message : "İndirme başarısız.");
    } finally {
      setDownloading(null);
    }
  }

  if (loading || !user) {
    return (
      <div className="state">
        <div className="spinner" />
      </div>
    );
  }

  return (
    <>
      <TopBar user={user} onLogout={logout} />
      <div className="container">
        <div className="breadcrumb">
          <Link href="/">Derslerim</Link> <span>/</span>{" "}
          <Link href={`/sinav/${examId}`}>Sınav</Link> <span>/</span> <span>Akreditasyon</span>
        </div>

        <div
          className="page-head"
          style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", gap: "1rem", flexWrap: "wrap" }}
        >
          <div>
            <p className="eyebrow">Akreditasyon</p>
            <h1>Kazanım Edinim Raporu</h1>
            {report && (
              <p className="sub">
                {report.course_code} — {report.course_name} · {report.exam_title}
                {report.department ? ` · ${report.department}` : ""}
              </p>
            )}
          </div>
          <div style={{ display: "flex", gap: ".6rem", flexWrap: "wrap" }}>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => download("grades")}
              disabled={downloading !== null}
            >
              {downloading === "grades" ? "İndiriliyor…" : "⬇ OBS Not Listesi"}
            </button>
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => download("accreditation")}
              disabled={downloading !== null}
            >
              {downloading === "accreditation" ? "İndiriliyor…" : "⬇ Kanıt Dosyası (Excel)"}
            </button>
          </div>
        </div>

        {error && <div className="error-box" style={{ marginBottom: "1rem" }}>{error}</div>}

        {dataLoading || !report ? (
          <div className="state">
            <div className="spinner" />
          </div>
        ) : (
          <>
            <div className="report-meta">
              <div className="meta-item">
                <span className="meta-lbl">Sınava giren</span>
                <span className="meta-val mono">
                  {report.attended_students} / {report.total_students}
                </span>
              </div>
              <div className="meta-item">
                <span className="meta-lbl">Notu onaylanmış</span>
                <span className="meta-val mono">{report.approved_students}</span>
              </div>
              <div className="meta-item threshold">
                <span className="meta-lbl">Edinim eşiği</span>
                <div className="threshold-control">
                  <input
                    type="range"
                    min={0}
                    max={100}
                    step={5}
                    value={threshold}
                    onChange={(e) => setThreshold(Number(e.target.value))}
                  />
                  <span className="meta-val mono">%{threshold}</span>
                </div>
              </div>
            </div>

            {report.warnings.length > 0 && (
              <div className="warnings">
                {report.warnings.map((w, i) => (
                  <div key={i} className="warn-row">
                    ⚠ {w}
                  </div>
                ))}
              </div>
            )}

            <OutcomeSection
              title="Program Öğrenme Çıktıları (PÇ)"
              note="MÜDEK / MEDEK bu seviyeyi denetler."
              items={report.program_outcomes}
            />
            <OutcomeSection
              title="Ders Öğrenme Çıktıları (DÇ)"
              note="Program çıktılarını besleyen ders kazanımları."
              items={report.course_outcomes}
            />
          </>
        )}
      </div>

      <style>{`
        .report-meta {
          display: flex; flex-wrap: wrap; gap: 1px; background: var(--hairline);
          border: 1px solid var(--hairline); border-radius: var(--radius); overflow: hidden; margin-bottom: 1.5rem;
        }
        .meta-item { background: var(--surface); padding: .9rem 1.2rem; flex: 1; min-width: 160px; }
        .meta-item.threshold { flex: 2; min-width: 240px; }
        .meta-lbl { display: block; font-size: .7rem; text-transform: uppercase; letter-spacing: .05em; color: var(--ink-3); margin-bottom: .35rem; }
        .meta-val { font-size: 1.3rem; font-weight: 600; }
        .threshold-control { display: flex; align-items: center; gap: .8rem; }
        .threshold-control input { flex: 1; accent-color: var(--red); }
        .warnings { display: flex; flex-direction: column; gap: .4rem; margin-bottom: 1.5rem; }
        .warn-row { background: var(--amber-soft); color: var(--amber); padding: .6rem .8rem; border-radius: var(--radius); font-size: .85rem; }
      `}</style>
    </>
  );
}

function OutcomeSection({
  title,
  note,
  items,
}: {
  title: string;
  note: string;
  items: Attainment[];
}) {
  if (items.length === 0) {
    return (
      <section style={{ marginBottom: "2rem" }}>
        <h2 style={{ fontSize: "1.15rem", marginBottom: ".3rem" }}>{title}</h2>
        <p style={{ color: "var(--ink-3)", fontSize: ".88rem" }}>
          Bu sınav hiçbir {title.includes("Program") ? "program" : "ders"} çıktısını
          ölçmüyor.
        </p>
      </section>
    );
  }
  return (
    <section style={{ marginBottom: "2rem" }}>
      <div style={{ marginBottom: ".9rem" }}>
        <h2 style={{ fontSize: "1.15rem" }}>{title}</h2>
        <p style={{ color: "var(--ink-3)", fontSize: ".82rem", marginTop: ".2rem" }}>{note}</p>
      </div>
      <div className="card" style={{ padding: "1.1rem 1.3rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
        {items.map((o) => (
          <div key={o.code} className="oc">
            <div className="oc-top">
              <span className="oc-code mono">{o.code}</span>
              <span className="oc-name">{o.description}</span>
              <span className={`badge ${o.is_attained ? "badge-approved" : "badge-failed"}`}>
                {o.is_attained ? "EDİNİLDİ" : "EDİNİLMEDİ"}
              </span>
            </div>
            <div className="oc-bar-row">
              <div className="oc-bar">
                <i
                  style={{
                    width: `${Math.min(o.pct, 100)}%`,
                    background: o.is_attained ? "var(--green)" : "var(--amber)",
                  }}
                />
                <span
                  className="oc-threshold"
                  style={{ left: `${o.threshold}%` }}
                  title={`eşik %${o.threshold}`}
                />
              </div>
              <span className="oc-pct mono">%{o.pct}</span>
            </div>
            <div className="oc-detail mono">
              {o.earned} / {o.possible} puan · Soru {o.question_numbers.join(", ") || "—"} ·{" "}
              {o.student_count} öğrenci
            </div>
          </div>
        ))}
      </div>

      <style>{`
        .oc { display: flex; flex-direction: column; gap: .5rem; }
        .oc:not(:last-child) { border-bottom: 1px solid var(--hairline); padding-bottom: 1rem; }
        .oc-top { display: grid; grid-template-columns: auto 1fr auto; gap: .7rem; align-items: center; }
        .oc-code { font-weight: 650; color: var(--ink-2); background: var(--surface-2); padding: .15rem .45rem; border-radius: 3px; font-size: .8rem; }
        .oc-name { font-size: .92rem; }
        .oc-bar-row { display: flex; align-items: center; gap: .8rem; }
        .oc-bar { position: relative; flex: 1; height: 10px; background: var(--surface-2); border-radius: 99px; overflow: hidden; }
        .oc-bar > i { position: absolute; inset: 0 auto 0 0; border-radius: 99px; }
        .oc-threshold { position: absolute; top: -2px; bottom: -2px; width: 2px; background: var(--ink-3); opacity: .6; }
        .oc-pct { font-size: .9rem; font-weight: 600; min-width: 3.2rem; text-align: right; }
        .oc-detail { font-size: .76rem; color: var(--ink-3); }
      `}</style>
    </section>
  );
}
