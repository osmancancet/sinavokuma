/*
  Core API istemcisi. Kurumun kendi sunucusundaki FastAPI'ye bağlanır (KVKK).
  JWT localStorage'da tutulur; her istekte Authorization header'ına eklenir.
*/

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const TOKEN_KEY = "sinavokuma_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${BASE}${path}`, { ...options, headers });

  if (res.status === 401) {
    clearToken();
    if (typeof window !== "undefined" && !window.location.pathname.startsWith("/giris")) {
      window.location.href = "/giris";
    }
    throw new ApiError(401, "Oturum süresi doldu.");
  }

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      /* boş gövde */
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

// ── Kimlik ─────────────────────────────────────────────────────────────
export interface Me {
  id: number;
  email: string;
  full_name: string;
  role: "ADMIN" | "TEACHER" | "AUDITOR";
  is_active: boolean;
}

export async function login(email: string, password: string): Promise<string> {
  // OAuth2PasswordRequestForm form-urlencoded bekliyor.
  const form = new URLSearchParams({ username: email, password });
  const res = await fetch(`${BASE}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body.detail ?? "Giriş başarısız.");
  }
  const data = await res.json();
  return data.access_token as string;
}

export const getMe = () => request<Me>("/api/v1/auth/me");

// ── Dersler / sınavlar ─────────────────────────────────────────────────
export interface Course {
  id: number;
  code: string;
  name: string;
  department_id: number | null;
  teacher_id: number;
}
export interface Exam {
  id: number;
  course_id: number;
  title: string;
  date: string | null;
  total_score: number;
  status: "DRAFT" | "PROCESSING" | "COMPLETED";
}

export const listCourses = () => request<Course[]>("/api/v1/courses");
export const listExams = (courseId: number) =>
  request<Exam[]>(`/api/v1/courses/${courseId}/exams`);

// ── Kağıtlar ───────────────────────────────────────────────────────────
export interface Paper {
  id: number;
  exam_id: number;
  student_no: string;
  image_url: string | null;
  status: "PENDING" | "AI_SCORED" | "APPROVED" | "FAILED";
  error_message: string | null;
}

export const listPapers = (examId: number) =>
  request<Paper[]>(`/api/v1/exams/${examId}/papers`);

// ── Değerlendirme ekranı ───────────────────────────────────────────────
export interface Score {
  id: number;
  question_id: number;
  ai_raw_text: string | null;
  ai_score: number | null;
  ai_reasoning: string | null;
  final_score: number | null;
  reviewed_by_id: number | null;
}
export interface ReviewScreen {
  paper_id: number;
  exam_id: number;
  student_no: string;
  status: Paper["status"];
  image_url: string;
  scores: Score[];
}

export const getReview = (paperId: number) =>
  request<ReviewScreen>(`/api/v1/papers/${paperId}/review`);

export const approvePaper = (
  paperId: number,
  decisions: { score_id: number; final_score: number }[],
) =>
  request<ReviewScreen>(`/api/v1/papers/${paperId}/approve`, {
    method: "POST",
    body: JSON.stringify({ decisions }),
  });

// ── Sorular ────────────────────────────────────────────────────────────
export interface Question {
  id: number;
  exam_id: number;
  question_number: number;
  max_score: number;
  prompt: string | null;
  expected_answer: string | null;
  rubric_criteria: { kriter: string; puan: number }[];
}

export const listQuestions = (examId: number) =>
  request<Question[]>(`/api/v1/exams/${examId}/questions`);

// ── Akreditasyon ───────────────────────────────────────────────────────
export interface Attainment {
  code: string;
  description: string;
  earned: number;
  possible: number;
  pct: number;
  student_count: number;
  question_numbers: number[];
  threshold: number;
  is_attained: boolean;
}
export interface AccreditationReport {
  exam_id: number;
  exam_title: string;
  course_code: string;
  course_name: string;
  department: string | null;
  attended_students: number;
  approved_students: number;
  total_students: number;
  program_outcomes: Attainment[];
  course_outcomes: Attainment[];
  unmapped_questions: number[];
  warnings: string[];
}

export const getAccreditation = (examId: number, threshold = 50) =>
  request<AccreditationReport>(
    `/api/v1/exams/${examId}/accreditation?threshold=${threshold}`,
  );

// Excel indirmeleri — token gerektirir, o yüzden blob olarak çekip indiriyoruz.
export async function downloadExcel(path: string, filename: string): Promise<void> {
  const token = getToken();
  const res = await fetch(`${BASE}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) throw new ApiError(res.status, "İndirme başarısız.");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
