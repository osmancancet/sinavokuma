import { useState } from "react";
import { ActivityIndicator, StyleSheet, Text, TextInput, TouchableOpacity, View } from "react-native";

import { config } from "../lib/config";
import { useApp } from "../store";
import { C } from "../theme";

export default function LoginScreen() {
  const { api, setSession } = useApp();
  const [apiUrl, setApiUrl] = useState(config.getApiUrl());
  const [email, setEmail] = useState(config.getEmail() ?? "");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit() {
    setError(null);
    setBusy(true);
    try {
      const url = apiUrl.trim();
      config.setApiUrl(url);
      api.setBaseUrl(url); // adres değiştiyse Api örneğini güncelle
      const token = await api.login(email.trim(), password);
      setSession(token, email.trim());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Giriş başarısız.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <View style={s.wrap}>
      <View style={s.card}>
        <Text style={s.brand}>Rubrik</Text>
        <Text style={s.title}>Sınav Tarayıcı</Text>
        <Text style={s.sub}>Kurum hesabınızla giriş yapın</Text>

        {error && (
          <View style={s.errorBox}>
            <Text style={s.errorText}>{error}</Text>
          </View>
        )}

        <Text style={s.label}>Sunucu adresi</Text>
        <TextInput
          style={s.input}
          value={apiUrl}
          onChangeText={setApiUrl}
          autoCapitalize="none"
          keyboardType="url"
          placeholder="http://kurum-sunucusu:8000"
          placeholderTextColor={C.ink3}
        />

        <Text style={s.label}>E-posta</Text>
        <TextInput
          style={s.input}
          value={email}
          onChangeText={setEmail}
          autoCapitalize="none"
          keyboardType="email-address"
          placeholder="hoca@uni.edu.tr"
          placeholderTextColor={C.ink3}
        />

        <Text style={s.label}>Parola</Text>
        <TextInput
          style={s.input}
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          placeholderTextColor={C.ink3}
        />

        <TouchableOpacity style={[s.btn, busy && s.btnDisabled]} onPress={submit} disabled={busy}>
          {busy ? <ActivityIndicator color="#fff" /> : <Text style={s.btnText}>Giriş yap</Text>}
        </TouchableOpacity>

        <Text style={s.note}>
          Çektiğiniz kağıtlar önce cihazınızda saklanır, bağlantı geldiğinde kurumunuzun
          sunucusuna aktarılır. Veriler dışarıya gitmez.
        </Text>
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  wrap: { flex: 1, backgroundColor: C.bg, justifyContent: "center", padding: 20 },
  card: { backgroundColor: C.surface, borderRadius: 12, padding: 24, borderWidth: 1, borderColor: C.hairline },
  brand: { color: C.ink, fontSize: 22, fontWeight: "600", textAlign: "center" },
  title: { color: C.ink, fontSize: 18, fontWeight: "600", textAlign: "center", marginTop: 12 },
  sub: { color: C.ink2, fontSize: 14, textAlign: "center", marginTop: 4, marginBottom: 20 },
  label: { color: C.ink2, fontSize: 13, fontWeight: "600", marginBottom: 6, marginTop: 12 },
  input: {
    backgroundColor: C.surface2, color: C.ink, borderRadius: 8, paddingHorizontal: 12,
    paddingVertical: 11, fontSize: 15, borderWidth: 1, borderColor: C.hairline,
  },
  btn: { backgroundColor: C.red, borderRadius: 8, paddingVertical: 13, alignItems: "center", marginTop: 22 },
  btnDisabled: { opacity: 0.6 },
  btnText: { color: "#fff", fontSize: 15, fontWeight: "600" },
  errorBox: { backgroundColor: "#33202B", borderRadius: 8, padding: 10, marginBottom: 8 },
  errorText: { color: C.red, fontSize: 13 },
  note: { color: C.ink3, fontSize: 12, textAlign: "center", marginTop: 20, lineHeight: 18 },
});
