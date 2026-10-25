"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Building2,
  GraduationCap,
  Upload,
  ShieldAlert,
  Network,
  FolderSearch,
  Bot,
  CheckCircle2,
  FileBarChart,
  Bell,
  ScrollText,
  Settings,
  LogOut,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { Logo } from "./Logo";
import { cn } from "@/lib/utils";
import { ROLE_LABELS } from "@/types";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard, roles: ["*"] },
  { href: "/institutions", label: "Institutions", icon: Building2, roles: ["SUPER_ADMIN", "AICTE_ADMIN", "AUDITOR", "FRAUD_ANALYST"] },
  { href: "/students", label: "Student Records", icon: GraduationCap, roles: ["SUPER_ADMIN", "AICTE_ADMIN", "AUDITOR", "FRAUD_ANALYST", "INSTITUTION_ADMIN"] },
  { href: "/upload", label: "Upload Studio", icon: Upload, roles: ["INSTITUTION_ADMIN"] },
  { href: "/duplicates", label: "Duplicates", icon: ShieldAlert, roles: ["SUPER_ADMIN", "AICTE_ADMIN", "FRAUD_ANALYST"] },
  { href: "/risk", label: "Risk Cases", icon: ShieldAlert, roles: ["SUPER_ADMIN", "AICTE_ADMIN", "FRAUD_ANALYST", "INSTITUTION_ADMIN"] },
  { href: "/graph", label: "Trust Graph", icon: Network, roles: ["SUPER_ADMIN", "AICTE_ADMIN", "FRAUD_ANALYST", "INSTITUTION_ADMIN"] },
  { href: "/cases", label: "Investigations", icon: FolderSearch, roles: ["SUPER_ADMIN", "AICTE_ADMIN", "FRAUD_ANALYST"] },
  { href: "/copilot", label: "AI Copilot", icon: Bot, roles: ["*"] },
  { href: "/verification", label: "Verification", icon: CheckCircle2, roles: ["*"] },
  { href: "/reports", label: "Reports", icon: FileBarChart, roles: ["SUPER_ADMIN", "AICTE_ADMIN", "AUDITOR"] },
  { href: "/audit", label: "Audit Log", icon: ScrollText, roles: ["SUPER_ADMIN", "AICTE_ADMIN", "AUDITOR"] },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  if (!user) return null;

  const visibleItems = navItems.filter(
    (item) => item.roles.includes("*") || item.roles.some((r) => user.roles.includes(r))
  );

  return (
    <aside
      className="fixed left-0 top-0 h-screen w-60 flex flex-col border-r z-30"
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      <div className="p-4 border-b" style={{ borderColor: "var(--border)" }}>
        <Logo />
      </div>

      <nav className="flex-1 overflow-y-auto py-2">
        {visibleItems.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-4 py-2.5 text-sm transition-colors",
                active ? "font-medium" : ""
              )}
              style={{
                background: active ? "rgba(6, 182, 212, 0.1)" : "transparent",
                color: active ? "#06b6d4" : "var(--muted)",
                borderLeft: active ? "3px solid #06b6d4" : "3px solid transparent",
              }}
            >
              <Icon size={18} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t p-4" style={{ borderColor: "var(--border)" }}>
        <div className="flex items-center gap-2 mb-3">
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold"
            style={{ background: "var(--accent)", color: "white" }}
          >
            {user.full_name.charAt(0)}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{user.full_name}</p>
            <p className="text-xs truncate" style={{ color: "var(--muted)" }}>
              {user.roles.map((r) => ROLE_LABELS[r] || r).join(", ")}
            </p>
          </div>
        </div>
        <button
          onClick={logout}
          className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm hover:bg-slate-700/50 transition-colors"
          style={{ color: "var(--muted)" }}
        >
          <LogOut size={16} />
          Logout
        </button>
      </div>
    </aside>
  );
}
