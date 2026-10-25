"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Building2,
  GraduationCap,
  Upload,
  CheckSquare,
  ShieldAlert,
  Network,
  FolderSearch,
  Bot,
  CheckCircle2,
  FileBarChart,
  ScrollText,
  Settings,
  LogOut,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { Logo } from "./Logo";
import { cn } from "@/lib/utils";
import { ROLE_LABELS } from "@/types";
import { useState } from "react";

export const navItems = [
  { href: "/", label: "Command Centre", icon: LayoutDashboard, roles: ["*"] },
  { href: "/institutions", label: "Institutions", icon: Building2, roles: ["SUPER_ADMIN", "AICTE_ADMIN", "AUDITOR", "FRAUD_ANALYST"] },
  { href: "/students", label: "Student Records", icon: GraduationCap, roles: ["SUPER_ADMIN", "AICTE_ADMIN", "AUDITOR", "FRAUD_ANALYST", "INSTITUTION_ADMIN"] },
  { href: "/upload", label: "Upload Studio", icon: Upload, roles: ["SUPER_ADMIN", "AICTE_ADMIN", "INSTITUTION_ADMIN"] },
  { href: "/validation", label: "Validation & Recon", icon: CheckSquare, roles: ["SUPER_ADMIN", "AICTE_ADMIN", "FRAUD_ANALYST", "INSTITUTION_ADMIN"] },
  { href: "/risk", label: "Risk Intelligence", icon: ShieldAlert, roles: ["SUPER_ADMIN", "AICTE_ADMIN", "FRAUD_ANALYST", "INSTITUTION_ADMIN"] },
  { href: "/duplicates", label: "Duplicate Registry", icon: ShieldAlert, roles: ["SUPER_ADMIN", "AICTE_ADMIN", "FRAUD_ANALYST"] },
  { href: "/graph", label: "Academic Trust Graph", icon: Network, roles: ["SUPER_ADMIN", "AICTE_ADMIN", "FRAUD_ANALYST", "INSTITUTION_ADMIN"] },
  { href: "/cases", label: "Investigation Cases", icon: FolderSearch, roles: ["SUPER_ADMIN", "AICTE_ADMIN", "FRAUD_ANALYST"] },
  { href: "/verification", label: "Verification Centre", icon: CheckCircle2, roles: ["*"] },
  { href: "/copilot", label: "AI Compliance Copilot", icon: Bot, roles: ["*"] },
  { href: "/reports", label: "Reports & Analytics", icon: FileBarChart, roles: ["SUPER_ADMIN", "AICTE_ADMIN", "AUDITOR"] },
  { href: "/audit", label: "Audit Trail", icon: ScrollText, roles: ["SUPER_ADMIN", "AICTE_ADMIN", "AUDITOR"] },
  { href: "/settings", label: "System Settings", icon: Settings, roles: ["SUPER_ADMIN", "AICTE_ADMIN"] },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [collapsed, setCollapsed] = useState(false);

  if (!user) return null;

  const visibleItems = navItems.filter(
    (item) => item.roles.includes("*") || item.roles.some((r) => user.roles.includes(r))
  );

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 h-screen flex flex-col border-r z-30 transition-all duration-300",
        collapsed ? "w-18" : "w-64"
      )}
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      <div className="p-4 border-b flex items-center justify-between" style={{ borderColor: "var(--border)" }}>
        <div className={cn("overflow-hidden transition-all duration-300", collapsed ? "w-0 opacity-0" : "w-auto opacity-100")}>
          <Logo />
        </div>
        {collapsed && (
          <div className="mx-auto text-cyan-400 font-bold text-lg flex items-center justify-center w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/20">
            <ShieldCheck size={20} />
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1 rounded-lg text-slate-400 hover:text-cyan-400 hover:bg-slate-800 transition-colors ml-auto"
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-1">
        {visibleItems.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              title={collapsed ? item.label : undefined}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all duration-150 group relative",
                active ? "font-semibold text-cyan-400" : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              )}
              style={{
                background: active ? "rgba(6, 182, 212, 0.12)" : undefined,
                border: active ? "1px solid rgba(6, 182, 212, 0.25)" : "1px solid transparent",
              }}
            >
              <Icon size={18} className={cn("shrink-0 transition-transform group-hover:scale-105", active ? "text-cyan-400" : "text-slate-400 group-hover:text-slate-200")} />
              {!collapsed && <span className="truncate">{item.label}</span>}
              {active && !collapsed && (
                <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 ml-auto" />
              )}
            </Link>
          );
        })}
      </nav>

      <div className="border-t p-3" style={{ borderColor: "var(--border)" }}>
        <div className={cn("flex items-center gap-2 mb-2 p-1.5 rounded-lg bg-slate-900/50 border border-slate-800/80", collapsed ? "justify-center" : "")}>
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold border shrink-0"
            style={{
              background: "rgba(6, 182, 212, 0.15)",
              borderColor: "rgba(6, 182, 212, 0.3)",
              color: "#06b6d4",
            }}
          >
            {user.full_name.charAt(0)}
          </div>
          {!collapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold truncate text-slate-200">{user.full_name}</p>
              <p className="text-[10px] truncate uppercase font-mono tracking-wider" style={{ color: "var(--accent)" }}>
                {user.roles.map((r) => ROLE_LABELS[r] || r).join(", ")}
              </p>
            </div>
          )}
        </div>
        <button
          onClick={logout}
          className={cn(
            "flex items-center gap-2 w-full px-3 py-2 rounded-lg text-xs font-medium hover:bg-rose-500/10 hover:text-rose-400 transition-colors text-slate-400",
            collapsed ? "justify-center" : ""
          )}
        >
          <LogOut size={16} />
          {!collapsed && <span>Sign Out</span>}
        </button>
      </div>
    </aside>
  );
}
