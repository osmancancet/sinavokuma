/*
  Anahtar-değer depolama soyutlaması.

  SRS §1.1 MMKV istiyor (çok hızlı yerel depolama). Ama MMKV native modül —
  Expo Go'da çalışmaz, dev build gerektirir ve test ortamında yoktur. Bu yüzden
  bir arayüz tanımlıyoruz: gerçek uygulamada MMKV, testte ve web'de bellek-içi.

  Bu, HTR motoru soyutlamasıyla aynı desen (services/inference/app/htr).
*/

export interface KeyValueStore {
  getString(key: string): string | undefined;
  set(key: string, value: string): void;
  delete(key: string): void;
  getAllKeys(): string[];
}

/** Test ve web için bellek-içi uygulama. Node'da da çalışır. */
export class MemoryStore implements KeyValueStore {
  private data = new Map<string, string>();
  getString(key: string) {
    return this.data.get(key);
  }
  set(key: string, value: string) {
    this.data.set(key, value);
  }
  delete(key: string) {
    this.data.delete(key);
  }
  getAllKeys() {
    return [...this.data.keys()];
  }
}

/**
 * MMKV uygulaması. Gerçek cihazda `react-native-mmkv` kurulu olduğunda kullanılır.
 * Modül yoksa (Expo Go, test) sessizce bellek-içine düşer — uygulama çökmez.
 */
export function createStore(): KeyValueStore {
  try {
    // Dinamik import: react-native-mmkv yoksa require patlar, catch'e düşeriz.
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const { MMKV } = require("react-native-mmkv");
    const mmkv = new MMKV({ id: "sinavokuma" });
    return {
      getString: (k) => mmkv.getString(k),
      set: (k, v) => mmkv.set(k, v),
      delete: (k) => mmkv.delete(k),
      getAllKeys: () => mmkv.getAllKeys(),
    };
  } catch {
    return new MemoryStore();
  }
}
