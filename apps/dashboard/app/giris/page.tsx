"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { login, setToken } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const token = await login(email.trim(), password);
      setToken(token);
      router.replace("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Giriş başarısız.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-wrap">
      <form className="login-card" onSubmit={submit}>
        <div className="brand" style={{ justifyContent: "center", marginBottom: "1.4rem" }}>
          <span className="brand-mark" aria-hidden="true" /> Rubrik
        </div>
        <h1 className="login-title">Değerlendirme Paneli</h1>
        <p className="login-sub">Kurum hesabınızla giriş yapın.</p>

        {error && (
          <div className="error-box" style={{ marginBottom: "1rem" }}>
            {error}
          </div>
        )}

        <label className="field">
          <span>E-posta</span>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoFocus
            placeholder="hoca@uni.edu.tr"
          />
        </label>
        <label className="field">
          <span>Parola</span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>

        <button type="submit" className="btn btn-primary" disabled={busy} style={{ width: "100%", marginTop: ".5rem" }}>
          {busy ? "Giriş yapılıyor…" : "Giriş yap"}
        </button>

        <p className="login-note">
          Öğrenci verileriniz kurumunuzun kendi sunucusunda işlenir. Bu panel dışarıya veri göndermez.
        </p>
      </form>

      <style>{`
        .login-wrap { min-height: 100dvh; display: grid; place-items: center; padding: 1.5rem; }
        .login-card {
          width: 100%; max-width: 400px;
          background: var(--surface); border: 1px solid var(--hairline);
          border-radius: 8px; box-shadow: var(--shadow); padding: 2rem;
        }
        .login-title { font-size: 1.4rem; text-align: center; }
        .login-sub { text-align: center; color: var(--ink-2); font-size: .9rem; margin: .3rem 0 1.5rem; }
        .field { display: block; margin-bottom: 1rem; }
        .field span { display: block; font-size: .82rem; font-weight: 600; color: var(--ink-2); margin-bottom: .35rem; }
        .field input {
          width: 100%; padding: .6rem .75rem; font-size: .95rem; font-family: inherit;
          background: var(--surface-2); color: var(--ink);
          border: 1px solid var(--hairline); border-radius: var(--radius);
        }
        .field input:focus { outline: 2px solid var(--red); outline-offset: 1px; border-color: transparent; }
        .login-note { font-size: .78rem; color: var(--ink-3); text-align: center; margin-top: 1.4rem; line-height: 1.5; }
      `}</style>
    </div>
  );
}
