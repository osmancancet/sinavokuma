import { useMemo, useState } from "react";
import { ActivityIndicator, FlatList, StyleSheet, Text, TouchableOpacity, View } from "react-native";

import type { PaperState, QueuedPaper } from "../lib/queue";
import { useApp } from "../store";
import { C } from "../theme";

/*
  SRS GÖREV 11 (arayüz) — Yükleme kuyruğu. Bekleyen kağıtları listeler, "Şimdi
  Senkronize Et" ile arka plan yüklemesini tetikler. Gerçek uygulamada bağlantı
  geldiğinde otomatik de tetiklenir (NetInfo dinleyicisi — dev build gerektirir).
*/

const STATE_META: Record<PaperState, { label: string; color: string }> = {
  QUEUED: { label: "Bekliyor", color: C.ink3 },
  UPLOADING: { label: "Yükleniyor", color: C.blue },
  UPLOADED: { label: "Yüklendi", color: C.green },
  FAILED: { label: "Başarısız", color: C.red },
};

export default function QueueScreen() {
  const { queue, counts, syncing, sync, refreshCounts } = useApp();
  const [, setTick] = useState(0);

  const papers = useMemo(() => queue.all(), [queue, counts, syncing]);
  const pending = counts.QUEUED + counts.FAILED;

  async function onSync() {
    await sync();
    setTick((t) => t + 1);
  }

  function clearUploaded() {
    for (const p of queue.all()) if (p.state === "UPLOADED") queue.remove(p.id);
    refreshCounts();
    setTick((t) => t + 1);
  }

  return (
    <View style={s.wrap}>
      <View style={s.summary}>
        <Stat n={counts.QUEUED} label="Bekliyor" color={C.ink3} />
        <Stat n={counts.UPLOADING} label="Yükleniyor" color={C.blue} />
        <Stat n={counts.UPLOADED} label="Yüklendi" color={C.green} />
        <Stat n={counts.FAILED} label="Başarısız" color={C.red} />
      </View>

      <View style={s.actions}>
        <TouchableOpacity
          style={[s.syncBtn, (syncing || pending === 0) && s.btnDisabled]}
          onPress={onSync}
          disabled={syncing || pending === 0}
        >
          {syncing ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={s.syncText}>
              {pending > 0 ? `${pending} kağıdı gönder` : "Gönderilecek kağıt yok"}
            </Text>
          )}
        </TouchableOpacity>
        {counts.UPLOADED > 0 && (
          <TouchableOpacity style={s.clearBtn} onPress={clearUploaded}>
            <Text style={s.clearText}>Yüklenenleri temizle</Text>
          </TouchableOpacity>
        )}
      </View>

      {papers.length === 0 ? (
        <View style={s.empty}>
          <Text style={s.emptyTitle}>Kuyruk boş</Text>
          <Text style={s.emptyText}>Tara sekmesinden kağıt çekin.</Text>
        </View>
      ) : (
        <FlatList
          data={papers}
          keyExtractor={(p) => p.id}
          contentContainerStyle={{ padding: 12 }}
          renderItem={({ item }) => <Row paper={item} />}
        />
      )}
    </View>
  );
}

function Stat({ n, label, color }: { n: number; label: string; color: string }) {
  return (
    <View style={s.stat}>
      <Text style={[s.statN, { color }]}>{n}</Text>
      <Text style={s.statL}>{label}</Text>
    </View>
  );
}

function Row({ paper }: { paper: QueuedPaper }) {
  const meta = STATE_META[paper.state];
  return (
    <View style={s.row}>
      <View style={{ flex: 1 }}>
        <Text style={s.rowNo}>{paper.studentNo}</Text>
        {paper.state === "FAILED" && paper.lastError && (
          <Text style={s.rowErr}>{paper.lastError}</Text>
        )}
      </View>
      <View style={[s.pill, { backgroundColor: meta.color + "22" }]}>
        <Text style={[s.pillText, { color: meta.color }]}>{meta.label}</Text>
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  wrap: { flex: 1, backgroundColor: C.bg },
  summary: {
    flexDirection: "row", backgroundColor: C.surface, borderBottomWidth: 1, borderBottomColor: C.hairline,
  },
  stat: { flex: 1, alignItems: "center", paddingVertical: 16 },
  statN: { fontSize: 24, fontWeight: "700" },
  statL: { color: C.ink3, fontSize: 11, marginTop: 2 },

  actions: { padding: 12, gap: 8 },
  syncBtn: { backgroundColor: C.red, borderRadius: 8, paddingVertical: 14, alignItems: "center" },
  btnDisabled: { opacity: 0.5 },
  syncText: { color: "#fff", fontSize: 15, fontWeight: "600" },
  clearBtn: { alignItems: "center", paddingVertical: 8 },
  clearText: { color: C.ink3, fontSize: 13 },

  empty: { flex: 1, justifyContent: "center", alignItems: "center", padding: 24 },
  emptyTitle: { color: C.ink2, fontSize: 16, fontWeight: "600" },
  emptyText: { color: C.ink3, fontSize: 13, marginTop: 4 },

  row: {
    flexDirection: "row", alignItems: "center", backgroundColor: C.surface,
    borderRadius: 8, padding: 14, marginBottom: 8, borderWidth: 1, borderColor: C.hairline,
  },
  rowNo: { color: C.ink, fontSize: 16, fontWeight: "600", letterSpacing: 1 },
  rowErr: { color: C.red, fontSize: 12, marginTop: 3 },
  pill: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 20 },
  pillText: { fontSize: 12, fontWeight: "600" },
});
