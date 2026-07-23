/*
  Core API istemcisi (mobil). FAZ 1'de yazdığımız presigned URL akışını izler:

    1. POST /exams/{id}/papers/upload-url  -> paper_id + imzalı PUT URL
    2. PUT <upload_url> (dosya)             -> DOĞRUDAN MinIO'ya (API'den geçmez)
    3. POST /papers/{id}/confirm            -> işleme kuyruğuna al

  Bu akış SRS §3.1'in "yüzlerce fotoğraf" senaryosu için kritik: dosya API
  sunucusundan geçmez, doğrudan nesne depolamaya gider.
*/

export interface ApiConfig {
  baseUrl: string;
  token: string | null;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export interface UploadUrlResponse {
  paper_id: number;
  object_key: string;
  upload_url: string;
  expires_in_seconds: number;
}

async function loginRequest(baseUrl: string, email: string, password: string): Promise<string> {
  const body = new URLSearchParams({ username: email, password });
  const res = await fetch(`${baseUrl}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: body.toString(),
  });
  if (!res.ok) {
    const b = await res.json().catch(() => ({}));
    throw new ApiError(res.status, b.detail ?? "Giriş başarısız.");
  }
  const data = await res.json();
  return data.access_token as string;
}

export class Api {
  constructor(private config: ApiConfig) {}

  setToken(token: string | null) {
    this.config.token = token;
  }

  setBaseUrl(baseUrl: string) {
    this.config.baseUrl = baseUrl;
  }

  login(email: string, password: string) {
    return loginRequest(this.config.baseUrl, email, password);
  }

  private authHeaders(): Record<string, string> {
    return this.config.token ? { Authorization: `Bearer ${this.config.token}` } : {};
  }

  /** 1. adım — kağıt kaydı aç, imzalı PUT URL al. */
  async requestUploadUrl(
    examId: number,
    studentNo: string,
    extension: string,
  ): Promise<UploadUrlResponse> {
    const res = await fetch(`${this.config.baseUrl}/api/v1/exams/${examId}/papers/upload-url`, {
      method: "POST",
      headers: { ...this.authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ student_no: studentNo, extension }),
    });
    if (!res.ok) {
      const b = await res.json().catch(() => ({}));
      throw new ApiError(res.status, b.detail ?? "Yükleme URL'i alınamadı.");
    }
    return res.json();
  }

  /** 2. adım — dosyayı DOĞRUDAN MinIO'ya PUT et (imzalı URL'e). */
  async uploadFile(uploadUrl: string, fileUri: string, mimeType: string): Promise<void> {
    // React Native fetch, file:// URI'lerini blob'a çevirebilir.
    const fileRes = await fetch(fileUri);
    const blob = await fileRes.blob();
    const res = await fetch(uploadUrl, {
      method: "PUT",
      headers: { "Content-Type": mimeType },
      body: blob,
    });
    if (!res.ok) {
      throw new ApiError(res.status, `Dosya yüklenemedi (HTTP ${res.status}).`);
    }
  }

  /** 3. adım — yükleme bitti, işleme kuyruğuna al. */
  async confirmUpload(paperId: number): Promise<void> {
    const res = await fetch(`${this.config.baseUrl}/api/v1/papers/${paperId}/confirm`, {
      method: "POST",
      headers: this.authHeaders(),
    });
    if (!res.ok) {
      const b = await res.json().catch(() => ({}));
      throw new ApiError(res.status, b.detail ?? "Onaylanamadı.");
    }
  }
}

export function mimeFor(extension: string): string {
  const e = extension.toLowerCase().replace(/^\./, "");
  if (e === "png") return "image/png";
  if (e === "webp") return "image/webp";
  if (e === "heic") return "image/heic";
  return "image/jpeg";
}
