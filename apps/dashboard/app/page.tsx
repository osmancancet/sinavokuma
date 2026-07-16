"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { listCourses, listExams, type Course, type Exam } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import TopBar from "./TopBar";

export default function HomePage() {
  const { user, loading, logout } = useAuth();
  const [courses, setCourses] = useState<Course[]>([]);
  const [examsByCourse, setExamsByCourse] = useState<Record<number, Exam[]>>({});
  const [dataLoading, setDataLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    listCourses()
      .then(async (cs) => {
        setCourses(cs);
        const entries = await Promise.all(
          cs.map(async (c) => [c.id, await listExams(c.id)] as const),
        );
        setExamsByCourse(Object.fromEntries(entries));
      })
      .catch((e) => setError(e.message))
      .finally(() => setDataLoading(false));
  }, [user]);

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
        <div className="page-head">
          <p className="eyebrow">Derslerim</p>
          <h1>Sınav Değerlendirme</h1>
          <p className="sub">
            Bir sınav seçip kağıtları değerlendirin, notları onaylayın, akreditasyon
            raporunu alın.
          </p>
        </div>

        {error && <div className="error-box">{error}</div>}

        {dataLoading ? (
          <div className="state">
            <div className="spinner" />
          </div>
        ) : courses.length === 0 ? (
          <div className="state">
            <h3>Henüz ders yok</h3>
            <p>Size atanmış bir ders bulunmuyor.</p>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
            {courses.map((course) => {
              const exams = examsByCourse[course.id] ?? [];
              return (
                <section key={course.id}>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "baseline",
                      gap: ".6rem",
                      marginBottom: ".8rem",
                    }}
                  >
                    <span className="mono" style={{ fontWeight: 650, color: "var(--blue)" }}>
                      {course.code}
                    </span>
                    <h2 style={{ fontSize: "1.2rem" }}>{course.name}</h2>
                  </div>

                  {exams.length === 0 ? (
                    <p style={{ color: "var(--ink-3)", fontSize: ".88rem" }}>
                      Bu derste henüz sınav yok.
                    </p>
                  ) : (
                    <div className="card">
                      <div className="list">
                        {exams.map((exam) => (
                          <Link
                            key={exam.id}
                            href={`/sinav/${exam.id}`}
                            className="list-row"
                            style={{ gridTemplateColumns: "1fr auto auto" }}
                          >
                            <div>
                              <div className="title">{exam.title}</div>
                              <div className="sub">
                                {exam.date ?? "Tarih belirtilmemiş"} · {exam.total_score} puan
                              </div>
                            </div>
                            <ExamStatusBadge status={exam.status} />
                            <span style={{ color: "var(--ink-3)" }}>→</span>
                          </Link>
                        ))}
                      </div>
                    </div>
                  )}
                </section>
              );
            })}
          </div>
        )}
      </div>
    </>
  );
}

function ExamStatusBadge({ status }: { status: Exam["status"] }) {
  const map = {
    DRAFT: { cls: "badge-pending", text: "Taslak" },
    PROCESSING: { cls: "badge-scored", text: "İşleniyor" },
    COMPLETED: { cls: "badge-approved", text: "Tamamlandı" },
  } as const;
  const { cls, text } = map[status];
  return <span className={`badge ${cls}`}>{text}</span>;
}
