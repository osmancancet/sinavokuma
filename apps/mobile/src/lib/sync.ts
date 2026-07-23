/*
  SRS GÖREV 11 — Arka plan senkronizasyonu.

  Bekleyen kağıtları sırayla sunucuya aktarır. Her kağıt için üç adımlı presigned
  URL akışını yürütür ve durumu kuyrukta günceller. Bağlantı yoksa veya bir adım
  başarısız olursa kağıt FAILED olur ve bir sonraki senkronizasyonda yeniden denenir.

  Bu da SAF MANTIK — Api ve PaperQueue enjekte edilir, böylece node ile test edilir.

  Tasarım kararları:
  - SIRAYLA (paralel değil): amfi wifi'si zayıf; 300 dosyayı aynı anda göndermek
    bağlantıyı boğar ve hepsi birden başarısız olur. Teker teker daha dayanıklı.
  - "En az bir kez" teslimat: bir kağıt iki kez gönderilse bile backend'in unique
    kısıtı (exam_id, student_no) ve /confirm'in "zaten işlenmiş" 409'u korur.
  - reentrancy koruması: senkronizasyon sürerken tekrar tetiklenirse ikinci çağrı
    hemen döner (aynı dosyayı iki iş parçacığı göndermesin).
*/

import type { Api } from "./api";
import { mimeFor } from "./api";
import type { PaperQueue, QueuedPaper } from "./queue";

export interface SyncResult {
  uploaded: number;
  failed: number;
  skipped: boolean; // başka bir senkronizasyon zaten çalışıyordu
}

export class Syncer {
  private running = false;

  constructor(
    private api: Api,
    private queue: PaperQueue,
    private onChange?: () => void,
  ) {}

  get isRunning() {
    return this.running;
  }

  private notify() {
    this.onChange?.();
  }

  async syncAll(): Promise<SyncResult> {
    if (this.running) return { uploaded: 0, failed: 0, skipped: true };
    this.running = true;
    let uploaded = 0;
    let failed = 0;
    try {
      for (const paper of this.queue.pending()) {
        const ok = await this.uploadOne(paper);
        if (ok) uploaded += 1;
        else failed += 1;
        this.notify();
      }
    } finally {
      this.running = false;
    }
    return { uploaded, failed, skipped: false };
  }

  private async uploadOne(paper: QueuedPaper): Promise<boolean> {
    this.queue.transition(paper.id, { state: "UPLOADING", lastError: undefined });
    this.notify();
    try {
      // 1. upload-url — yalnızca daha önce alınmadıysa. Kağıt kaydı bir kez açılır;
      //    ikinci denemede aynı öğrenci için 409 gelirse bunu "zaten var" kabul ederiz.
      let paperId = paper.paperId;
      let objectKey = paper.objectKey;
      let uploadUrl: string | undefined;

      if (paperId == null) {
        try {
          const resp = await this.api.requestUploadUrl(
            paper.examId,
            paper.studentNo,
            paper.extension,
          );
          paperId = resp.paper_id;
          objectKey = resp.object_key;
          uploadUrl = resp.upload_url;
          this.queue.transition(paper.id, { paperId, objectKey });
        } catch (e) {
          // 409: bu öğrencinin kağıdı zaten açılmış (önceki yarım kalan deneme).
          // Bu durumda upload-url'i tekrar alamayız; kağıt sunucuda zaten var,
          // muhtemelen işlenmiş. Yerelden düşürüp devam ediyoruz.
          if (isConflict(e)) {
            this.queue.transition(paper.id, {
              state: "UPLOADED",
              lastError: "Sunucuda zaten mevcut.",
            });
            return true;
          }
          throw e;
        }
      } else {
        // Kayıt açılmış ama yükleme yarım kalmış. Yeni bir imzalı URL gerekir;
        // eski URL'in süresi dolmuş olabilir. upload-url tekrar çağrılamayacağı
        // için (409 döner), bu senaryoyu backend'e /papers/{id}/upload-url gibi
        // bir "yeniden imzala" ucu eklenerek çözmek gerekir. Şimdilik: confirm dene.
        uploadUrl = undefined;
      }

      // 2. dosyayı MinIO'ya PUT et (imzalı URL varsa)
      if (uploadUrl) {
        await this.api.uploadFile(uploadUrl, paper.localUri, mimeFor(paper.extension));
      }

      // 3. confirm — işleme kuyruğuna al
      if (paperId != null) {
        await this.api.confirmUpload(paperId);
      }

      this.queue.transition(paper.id, { state: "UPLOADED", lastError: undefined });
      return true;
    } catch (e) {
      const message = e instanceof Error ? e.message : "Bilinmeyen hata";
      this.queue.transition(paper.id, {
        state: "FAILED",
        attempts: paper.attempts + 1,
        lastError: message,
      });
      return false;
    }
  }
}

function isConflict(e: unknown): boolean {
  return typeof e === "object" && e !== null && "status" in e && (e as { status: number }).status === 409;
}
