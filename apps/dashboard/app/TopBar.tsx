"use client";

import Link from "next/link";

import type { Me } from "@/lib/api";

const ROLE_LABEL: Record<Me["role"], string> = {
  ADMIN: "Yönetici",
  TEACHER: "Öğretim Görevlisi",
  AUDITOR: "Denetçi",
};

export default function TopBar({ user, onLogout }: { user: Me | null; onLogout: () => void }) {
  return (
    <div className="topbar">
      <Link href="/" className="brand" style={{ textDecoration: "none", color: "inherit" }}>
        <span className="brand-mark" aria-hidden="true" /> Rubrik
      </Link>
      {user && (
        <div className="topbar-user">
          <span className="role-chip">{ROLE_LABEL[user.role]}</span>
          <span>{user.full_name}</span>
          <button type="button" className="btn btn-ghost btn-sm" onClick={onLogout}>
            Çıkış
          </button>
        </div>
      )}
    </div>
  );
}
