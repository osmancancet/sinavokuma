/*
  Çevrimdışı kuyruk + senkronizasyon testleri. SAF MANTIK olduğu için node ile
  çalışır (cihaz gerekmez):

    npx tsx src/lib/sync.test.ts

  Sahte bir Api ile ağ davranışını taklit ediyoruz: bağlantı yok, sonra var,
  mükerrer gönderim, kısmi başarısızlık. Bunlar mobil tarafın en kritik yolları —
  bir kağıt sessizce kaybolursa öğrencinin sınavı hiç okunmaz.
*/

import { Api } from "./api";
import { PaperQueue } from "./queue";
import { MemoryStore } from "./storage";
import { Syncer } from "./sync";

let passed = 0;
let failed = 0;
function assert(cond: boolean, msg: string) {
  if (cond) {
    passed += 1;
    console.log(`  ✓ ${msg}`);
  } else {
    failed += 1;
    console.error(`  ✗ ${msg}`);
  }
}

// Sahte Api — gerçek ağ yerine kontrol edilebilir davranış.
class FakeApi extends Api {
  online = true;
  uploadUrlCalls = 0;
  confirmCalls = 0;
  putCalls = 0;
  nextPaperId = 100;
  conflictFor = new Set<string>(); // "examId:studentNo" -> 409 dönsün

  constructor() {
    super({ baseUrl: "http://fake", token: "t" });
  }

  async requestUploadUrl(examId: number, studentNo: string, extension: string) {
    this.uploadUrlCalls += 1;
    if (!this.online) throw new Error("Ağ yok");
    if (this.conflictFor.has(`${examId}:${studentNo}`)) {
      const err = new Error("Zaten var") as Error & { status: number };
      err.status = 409;
      throw err;
    }
    const id = this.nextPaperId++;
    return {
      paper_id: id,
      object_key: `exams/${examId}/papers/${studentNo}.${extension}`,
      upload_url: `http://fake/put/${id}`,
      expires_in_seconds: 900,
    };
  }
  async uploadFile() {
    this.putCalls += 1;
    if (!this.online) throw new Error("Ağ yok");
  }
  async confirmUpload() {
    this.confirmCalls += 1;
    if (!this.online) throw new Error("Ağ yok");
  }
}

function makeQueue() {
  return new PaperQueue(new MemoryStore());
}

async function testHappyPath() {
  console.log("\n[1] Bağlantı varken: kağıt yüklenir ve UPLOADED olur");
  const q = makeQueue();
  const api = new FakeApi();
  const sync = new Syncer(api, q);

  q.enqueue({ id: "a", examId: 1, studentNo: "111", localUri: "file://a.jpg", extension: "jpg", createdAt: 1 });
  const res = await sync.syncAll();

  assert(res.uploaded === 1 && res.failed === 0, "1 kağıt yüklendi");
  assert(q.get("a")!.state === "UPLOADED", "durum UPLOADED");
  assert(q.get("a")!.paperId === 100, "sunucu paper_id kaydedildi");
  assert(api.uploadUrlCalls === 1 && api.putCalls === 1 && api.confirmCalls === 1, "3 adım da bir kez çağrıldı");
}

async function testOffline() {
  console.log("\n[2] Bağlantı yokken: kağıt kaybolmaz, FAILED olur, sonra başarır");
  const q = makeQueue();
  const api = new FakeApi();
  api.online = false;
  const sync = new Syncer(api, q);

  q.enqueue({ id: "b", examId: 1, studentNo: "222", localUri: "file://b.jpg", extension: "jpg", createdAt: 1 });
  const r1 = await sync.syncAll();
  assert(r1.failed === 1, "çevrimdışıyken başarısız");
  assert(q.get("b")!.state === "FAILED", "durum FAILED (kaybolmadı)");
  assert(q.get("b") !== undefined, "kağıt hâlâ kuyrukta");

  // Bağlantı geldi
  api.online = true;
  const r2 = await sync.syncAll();
  assert(r2.uploaded === 1, "bağlantı gelince yeniden denenip yüklendi");
  assert(q.get("b")!.state === "UPLOADED", "durum UPLOADED");
}

async function testDuplicateConflict() {
  console.log("\n[3] Aynı öğrencinin kağıdı sunucuda zaten varsa (409): çift işlenmez");
  const q = makeQueue();
  const api = new FakeApi();
  api.conflictFor.add("1:333");
  const sync = new Syncer(api, q);

  q.enqueue({ id: "c", examId: 1, studentNo: "333", localUri: "file://c.jpg", extension: "jpg", createdAt: 1 });
  const res = await sync.syncAll();
  assert(res.uploaded === 1, "409 'başarılı' sayıldı (sunucuda zaten var)");
  assert(q.get("c")!.state === "UPLOADED", "durum UPLOADED");
  assert(api.putCalls === 0 && api.confirmCalls === 0, "dosya tekrar gönderilmedi");
}

async function testReentrancy() {
  console.log("\n[4] Senkronizasyon çalışırken tekrar tetiklenirse: ikinci çağrı atlanır");
  const q = makeQueue();
  const api = new FakeApi();
  const sync = new Syncer(api, q);
  q.enqueue({ id: "d", examId: 1, studentNo: "444", localUri: "file://d.jpg", extension: "jpg", createdAt: 1 });

  const [r1, r2] = await Promise.all([sync.syncAll(), sync.syncAll()]);
  const skipped = r1.skipped || r2.skipped;
  assert(skipped, "ikinci eşzamanlı çağrı atlandı (skipped)");
  assert(api.uploadUrlCalls === 1, "kağıt yalnızca bir kez gönderildi");
}

async function testOrdering() {
  console.log("\n[5] Kağıtlar çekilme sırasıyla gönderilir");
  const q = makeQueue();
  q.enqueue({ id: "z", examId: 1, studentNo: "3", localUri: "f", extension: "jpg", createdAt: 30 });
  q.enqueue({ id: "x", examId: 1, studentNo: "1", localUri: "f", extension: "jpg", createdAt: 10 });
  q.enqueue({ id: "y", examId: 1, studentNo: "2", localUri: "f", extension: "jpg", createdAt: 20 });
  const order = q.pending().map((p) => p.studentNo);
  assert(JSON.stringify(order) === JSON.stringify(["1", "2", "3"]), `sıra createdAt'e göre: ${order}`);
}

(async () => {
  console.log("=== Çevrimdışı kuyruk + senkronizasyon testleri ===");
  await testHappyPath();
  await testOffline();
  await testDuplicateConflict();
  await testReentrancy();
  await testOrdering();
  console.log(`\n${passed} geçti, ${failed} kaldı`);
  process.exit(failed === 0 ? 0 : 1);
})();
