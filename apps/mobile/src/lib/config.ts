import { createStore, type KeyValueStore } from "./storage";

/*
  Uygulama yapılandırması ve kalıcı oturum. API adresi, JWT ve seçili sınav
  yerel depoda (MMKV) saklanır — böylece uygulama kapansa da akademisyen
  yeniden giriş yapmadan kaldığı yerden devam eder.
*/

export const store: KeyValueStore = createStore();

const KEYS = {
  apiUrl: "cfg:apiUrl",
  token: "cfg:token",
  email: "cfg:email",
  examId: "cfg:examId",
} as const;

// Geliştirmede yerel API. Gerçek kurulumda kurumun sunucu adresi girilir.
const DEFAULT_API_URL = "http://localhost:8000";

export const config = {
  getApiUrl: () => store.getString(KEYS.apiUrl) ?? DEFAULT_API_URL,
  setApiUrl: (v: string) => store.set(KEYS.apiUrl, v),

  getToken: () => store.getString(KEYS.token) ?? null,
  setToken: (v: string | null) => (v ? store.set(KEYS.token, v) : store.delete(KEYS.token)),

  getEmail: () => store.getString(KEYS.email) ?? null,
  setEmail: (v: string) => store.set(KEYS.email, v),

  getExamId: () => {
    const v = store.getString(KEYS.examId);
    return v ? Number(v) : null;
  },
  setExamId: (v: number) => store.set(KEYS.examId, String(v)),
};
