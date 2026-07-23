import { CameraView, useCameraPermissions } from "expo-camera";
import { useRef, useState } from "react";
import { ActivityIndicator, StyleSheet, Text, TextInput, TouchableOpacity, View } from "react-native";

import { getScanner } from "../lib/scanner";
import { useApp } from "../store";
import { C } from "../theme";

/*
  SRS GÖREV 10 — Kamera ekranı. Akış:
    öğrenci no gir → fotoğraf çek → belge tarayıcı işler → kuyruğa ekle (yerel)
  Kuyruk çevrimdışı çalışır; yükleme arka planda (KuyrukEkranı).

  Ergonomi (SRS §3.1 "tek elle kullanım"): büyük çekim butonu altta, öğrenci no
  girişi üstte. Çekimden sonra öğrenci no otomatik temizlenir, sıradaki kağıda hazır.
*/

export default function CameraScreen() {
  const { examId, queue, refreshCounts } = useApp();
  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef<CameraView>(null);
  const [studentNo, setStudentNo] = useState("");
  const [busy, setBusy] = useState(false);
  const [flash, setFlash] = useState<string | null>(null);

  if (!permission) {
    return (
      <View style={s.center}>
        <ActivityIndicator color={C.red} />
      </View>
    );
  }

  if (!permission.granted) {
    return (
      <View style={s.center}>
        <Text style={s.permTitle}>Kamera izni gerekli</Text>
        <Text style={s.permText}>Sınav kağıtlarını taramak için kamera erişimine izin verin.</Text>
        <TouchableOpacity style={s.btn} onPress={requestPermission}>
          <Text style={s.btnText}>İzin ver</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (examId == null) {
    return (
      <View style={s.center}>
        <Text style={s.permTitle}>Sınav seçilmedi</Text>
        <Text style={s.permText}>
          Kağıt taramadan önce bir sınav seçmelisiniz. (Sınav seçimi ekranı web
          panelinden yönetilir; burada geliştirme için sabit sınav kullanılıyor.)
        </Text>
      </View>
    );
  }

  async function capture() {
    const no = studentNo.trim();
    if (!no) {
      setFlash("Önce öğrenci numarası girin.");
      setTimeout(() => setFlash(null), 1500);
      return;
    }
    if (!cameraRef.current) return;
    setBusy(true);
    try {
      const photo = await cameraRef.current.takePictureAsync({ quality: 0.8 });
      if (!photo) throw new Error("Fotoğraf alınamadı.");

      // Belge tarayıcıdan geçir (şu an ham; OpenCV sonra takılacak).
      const scan = await getScanner().process(photo.uri);

      // Kuyruğa ekle — YEREL. İnternet olmasa da kaybolmaz (SRS §3.1).
      queue.enqueue({
        id: `${examId}-${no}-${Date.now()}`,
        examId: examId as number,
        studentNo: no,
        localUri: scan.uri,
        extension: "jpg",
        createdAt: Date.now(),
      });
      refreshCounts();

      setStudentNo(""); // sıradaki kağıda hazır
      setFlash(`✓ ${no} kuyruğa eklendi`);
      setTimeout(() => setFlash(null), 1500);
    } catch (e) {
      setFlash(e instanceof Error ? e.message : "Çekim başarısız.");
      setTimeout(() => setFlash(null), 2000);
    } finally {
      setBusy(false);
    }
  }

  return (
    <View style={s.wrap}>
      <View style={s.topBar}>
        <Text style={s.topLabel}>Öğrenci No</Text>
        <TextInput
          style={s.noInput}
          value={studentNo}
          onChangeText={setStudentNo}
          placeholder="20210777"
          placeholderTextColor={C.ink3}
          keyboardType="number-pad"
          returnKeyType="done"
        />
      </View>

      <View style={s.cameraBox}>
        <CameraView ref={cameraRef} style={StyleSheet.absoluteFill} facing="back" />
        {/* Kağıt hizalama çerçevesi — A4 oranına yakın */}
        <View style={s.frame} pointerEvents="none" />
        {flash && (
          <View style={s.flash} pointerEvents="none">
            <Text style={s.flashText}>{flash}</Text>
          </View>
        )}
      </View>

      <View style={s.bottomBar}>
        <TouchableOpacity
          style={[s.shutter, busy && s.shutterBusy]}
          onPress={capture}
          disabled={busy}
          accessibilityLabel="Kağıt çek"
        >
          {busy ? <ActivityIndicator color="#fff" /> : <View style={s.shutterInner} />}
        </TouchableOpacity>
        <Text style={s.hint}>Kağıdı çerçeveye hizalayıp çekin</Text>
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  wrap: { flex: 1, backgroundColor: "#000" },
  center: { flex: 1, backgroundColor: C.bg, justifyContent: "center", alignItems: "center", padding: 24 },
  permTitle: { color: C.ink, fontSize: 18, fontWeight: "600", marginBottom: 8 },
  permText: { color: C.ink2, fontSize: 14, textAlign: "center", lineHeight: 20, marginBottom: 20 },
  btn: { backgroundColor: C.red, borderRadius: 8, paddingVertical: 12, paddingHorizontal: 24 },
  btnText: { color: "#fff", fontWeight: "600" },

  topBar: {
    flexDirection: "row", alignItems: "center", gap: 12,
    paddingHorizontal: 16, paddingVertical: 12, backgroundColor: C.surface,
  },
  topLabel: { color: C.ink2, fontSize: 13, fontWeight: "600" },
  noInput: {
    flex: 1, backgroundColor: C.surface2, color: C.ink, borderRadius: 8,
    paddingHorizontal: 12, paddingVertical: 9, fontSize: 17, letterSpacing: 1,
    borderWidth: 1, borderColor: C.hairline,
  },

  cameraBox: { flex: 1, position: "relative" },
  frame: {
    position: "absolute", top: "8%", bottom: "8%", left: "6%", right: "6%",
    borderWidth: 2, borderColor: "rgba(255,255,255,.6)", borderRadius: 6,
  },
  flash: {
    position: "absolute", bottom: 20, left: 0, right: 0, alignItems: "center",
  },
  flashText: {
    color: "#fff", backgroundColor: "rgba(20,29,52,.9)", paddingHorizontal: 16,
    paddingVertical: 8, borderRadius: 20, fontSize: 14, overflow: "hidden",
  },

  bottomBar: { backgroundColor: C.surface, paddingVertical: 18, alignItems: "center" },
  shutter: {
    width: 72, height: 72, borderRadius: 36, backgroundColor: C.red,
    justifyContent: "center", alignItems: "center", borderWidth: 4, borderColor: "rgba(236,106,87,.3)",
  },
  shutterBusy: { opacity: 0.7 },
  shutterInner: { width: 56, height: 56, borderRadius: 28, backgroundColor: "#fff" },
  hint: { color: C.ink3, fontSize: 12, marginTop: 8 },
});
