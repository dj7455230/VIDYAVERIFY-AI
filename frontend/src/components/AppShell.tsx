"use client";

import { useAuth } from "@/contexts/AuthContext";
import { Sidebar } from "./Sidebar";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Bell, Search, ShieldCheck, HelpCircle } from "lucide-react";
import Link from "next/link";

export function AppShell({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [user, loading, router]);

  const handleGlobalSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    router.push(`/students?search=${encodeURIComponent(searchQuery.trim())}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950">
        <div className="text-center">
          <div
            className="w-10 h-10 border-2 rounded-full mx-auto mb-4 animate-spin"
            style={{ borderColor: "var(--accent)", borderTopColor: "transparent" }}
          />
          <p className="text-sm font-medium tracking-wide text-slate-300">
            Initializing VIDYAVERIFY AI Engine...
          </p>
          <p className="text-xs text-slate-500 mt-1">SIH26263 Institutional Trust Platform</p>
        </div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="min-h-screen flex bg-[#090d16] text-slate-100">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 ml-64 transition-all duration-300">
        {/* Top Header Bar */}
        <header
          className="sticky top-0 z-20 h-14 border-b px-6 flex items-center justify-between backdrop-blur-md"
          style={{
            background: "rgba(15, 23, 42, 0.8)",
            borderColor: "var(--border)",
          }}
        >
          <div className="flex items-center gap-4 flex-1 max-w-xl">
            <form onSubmit={handleGlobalSearch} className="relative w-full">
              <Search
                size={15}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
              />
              <input
                type="text"
                placeholder="Search APAAR ID, Student name, Roll number, or Institution code..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-1.5 rounded-lg text-xs border border-slate-700 bg-slate-900/60 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/70 focus:ring-1 focus:ring-cyan-500/30 transition-all"
              />
            </form>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-cyan-500/30 bg-cyan-500/10 text-cyan-400 text-[11px] font-semibold tracking-wide">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
              SYNTHETIC DEMONSTRATION DATA
            </div>

            <Link
              href="/copilot"
              className="px-2.5 py-1 rounded-lg text-xs font-medium border border-slate-700 text-slate-300 hover:text-cyan-400 hover:border-cyan-500/40 transition-colors flex items-center gap-1.5"
            >
              <span>Copilot</span>
            </Link>

            <Link
              href="/audit"
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
              title="Audit trail"
            >
              <Bell size={16} />
            </Link>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-6 max-w-7xl w-full mx-auto">{children}</main>
      </div>
    </div>
  );
}
