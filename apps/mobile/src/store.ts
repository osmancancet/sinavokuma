import { create } from "zustand";

import { Api } from "./lib/api";
import { config, store as kv } from "./lib/config";
import { PaperQueue, type PaperState } from "./lib/queue";
import { Syncer } from "./lib/sync";

/*
  Uygulama durumu (Zustand — SRS §1.1). Api, kuyruk ve senkronizasyon örneklerini
  tek yerde tutar; ekranlar bunları buradan alır.
*/

const api = new Api({ baseUrl: config.getApiUrl(), token: config.getToken() });
const queue = new PaperQueue(kv);

interface AppState {
  token: string | null;
  email: string | null;
  examId: number | null;
  counts: Record<PaperState, number>;
  syncing: boolean;

  api: Api;
  queue: PaperQueue;
  syncer: Syncer;

  refreshCounts: () => void;
  setSession: (token: string, email: string) => void;
  logout: () => void;
  setExamId: (id: number) => void;
  sync: () => Promise<void>;
}

export const useApp = create<AppState>((set, get) => {
  const syncer = new Syncer(api, queue, () => {
    // Her kağıt durumu değiştiğinde sayaçları tazele (UI canlı güncellensin).
    set({ counts: queue.counts(), syncing: syncer.isRunning });
  });

  return {
    token: config.getToken(),
    email: config.getEmail(),
    examId: config.getExamId(),
    counts: queue.counts(),
    syncing: false,
    api,
    queue,
    syncer,

    refreshCounts: () => set({ counts: queue.counts() }),

    setSession: (token, email) => {
      config.setToken(token);
      config.setEmail(email);
      api.setToken(token);
      set({ token, email });
    },

    logout: () => {
      config.setToken(null);
      api.setToken(null);
      set({ token: null });
    },

    setExamId: (id) => {
      config.setExamId(id);
      set({ examId: id });
    },

    sync: async () => {
      set({ syncing: true });
      await get().syncer.syncAll();
      set({ counts: queue.counts(), syncing: false });
    },
  };
});
