/*
  SRS §3.1 + GÖREV 10/11 — Çevrimdışı yükleme kuyruğu.

  Senaryo: akademisyen amfide, internet yok. Yüzlerce kağıt çekiyor. Her kağıt
  önce YERELE kaydedilir (MMKV), bağlantı gelince arka planda sunucuya aktarılır.
  İnternet kesikken hiçbir kağıt kaybolmamalı.

  Bu dosya SAF MANTIK — hiçbir React/Expo/native bağımlılığı yok. Bu yüzden node
  ile test edilebilir (queue.test.ts). Ürünün en kritik parçası: bir kağıt yükleme
  kaydı sessizce kaybolursa o öğrencinin sınavı hiç okunmaz ve kimse fark etmez.

  Durum makinesi:
    QUEUED    -> yerelde bekliyor, henüz gönderilmedi
    UPLOADING -> sunucuya aktarılıyor
    UPLOADED  -> MinIO'ya yüklendi, /confirm çağrıldı, sunucuda işlemde
    FAILED    -> deneme başarısız (geçici); yeniden denenecek
*/

import type { KeyValueStore } from "./storage";

export type PaperState = "QUEUED" | "UPLOADING" | "UPLOADED" | "FAILED";

export interface QueuedPaper {
  id: string; // yerel benzersiz id (cihazda üretilir)
  examId: number;
  studentNo: string;
  localUri: string; // cihazdaki dosya yolu (file://...)
  extension: string;
  state: PaperState;
  attempts: number;
  lastError?: string;
  createdAt: number;
  // Sunucu tarafı, upload-url alındıktan sonra doldurulur:
  paperId?: number;
  objectKey?: string;
}

const KEY_PREFIX = "paper:";

export class PaperQueue {
  constructor(private store: KeyValueStore) {}

  private key(id: string) {
    return `${KEY_PREFIX}${id}`;
  }

  /** Yeni bir kağıdı kuyruğa ekler (fotoğraf çekildiğinde). */
  enqueue(input: {
    id: string;
    examId: number;
    studentNo: string;
    localUri: string;
    extension: string;
    createdAt: number;
  }): QueuedPaper {
    const paper: QueuedPaper = {
      ...input,
      state: "QUEUED",
      attempts: 0,
    };
    this.save(paper);
    return paper;
  }

  save(paper: QueuedPaper): void {
    this.store.set(this.key(paper.id), JSON.stringify(paper));
  }

  get(id: string): QueuedPaper | undefined {
    const raw = this.store.getString(this.key(id));
    return raw ? (JSON.parse(raw) as QueuedPaper) : undefined;
  }

  remove(id: string): void {
    this.store.delete(this.key(id));
  }

  all(): QueuedPaper[] {
    return this.store
      .getAllKeys()
      .filter((k) => k.startsWith(KEY_PREFIX))
      .map((k) => JSON.parse(this.store.getString(k)!) as QueuedPaper)
      .sort((a, b) => a.createdAt - b.createdAt);
  }

  /** Gönderilmeyi bekleyenler: yeni çekilmiş veya başarısız olup yeniden denenecek. */
  pending(): QueuedPaper[] {
    return this.all().filter((p) => p.state === "QUEUED" || p.state === "FAILED");
  }

  counts(): Record<PaperState, number> {
    const acc: Record<PaperState, number> = {
      QUEUED: 0,
      UPLOADING: 0,
      UPLOADED: 0,
      FAILED: 0,
    };
    for (const p of this.all()) acc[p.state] += 1;
    return acc;
  }

  transition(id: string, patch: Partial<QueuedPaper>): QueuedPaper | undefined {
    const paper = this.get(id);
    if (!paper) return undefined;
    const next = { ...paper, ...patch };
    this.save(next);
    return next;
  }
}
