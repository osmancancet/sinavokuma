"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { clearToken, getMe, getToken, type Me } from "./api";

/**
 * Oturum durumunu yönetir. Token yoksa /giris'e atar.
 * `require=false` ile (login sayfası) sadece durumu okur, yönlendirmez.
 */
export function useAuth(require = true) {
  const router = useRouter();
  const [user, setUser] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    const token = getToken();
    if (!token) {
      setLoading(false);
      if (require) router.replace("/giris");
      return;
    }
    getMe()
      .then((me) => {
        if (alive) setUser(me);
      })
      .catch(() => {
        clearToken();
        if (require) router.replace("/giris");
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [require, router]);

  const logout = () => {
    clearToken();
    router.replace("/giris");
  };

  return { user, loading, logout };
}
