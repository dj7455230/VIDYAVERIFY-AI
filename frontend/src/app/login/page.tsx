"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { Logo } from "@/components/Logo";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      router.push("/");
    } catch (err: any) {
      setError(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const fillDemo = (em: string) => {
    setEmail(em);
    setPassword("Demo@2026");
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div
        className="w-full max-w-md"
        style={{ background: "var(--surface)" }}
      >
        <div className="p-8 rounded-xl border" style={{ borderColor: "var(--border)" }}>
          <div className="flex justify-center mb-6">
            <Logo />
          </div>
          <p className="text-center text-sm mb-6" style={{ color: "var(--muted)" }}>
            Sign in to your account
          </p>

          <div
            className="mb-4 p-3 rounded-lg text-center text-xs border"
            style={{
              background: "rgba(6, 182, 212, 0.08)",
              borderColor: "rgba(6, 182, 212, 0.3)",
              color: "#06b6d4",
            }}
          >
            SYNTHETIC DEMONSTRATION DATA — Local demo only
          </div>

          {error && (
            <div
              className="mb-4 p-3 rounded-lg text-sm text-center border"
              style={{
                background: "rgba(239, 68, 68, 0.1)",
                borderColor: "rgba(239, 68, 68, 0.3)",
                color: "#ef4444",
              }}
            >
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label
                className="block text-sm font-medium mb-1.5"
                style={{ color: "var(--foreground)" }}
              >
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoFocus
                className="w-full px-3 py-2 rounded-lg text-sm"
                style={{
                  background: "var(--background)",
                  border: "1px solid var(--border)",
                  color: "var(--foreground)",
                }}
                placeholder="you@example.com"
              />
            </div>
            <div>
              <label
                className="block text-sm font-medium mb-1.5"
                style={{ color: "var(--foreground)" }}
              >
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full px-3 py-2 rounded-lg text-sm"
                style={{
                  background: "var(--background)",
                  border: "1px solid var(--border)",
                  color: "var(--foreground)",
                }}
                placeholder="••••••••"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg font-medium text-sm transition-colors disabled:opacity-50"
              style={{
                background: "var(--accent)",
                color: "white",
              }}
            >
              {loading ? "Signing in..." : "Sign In"}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t" style={{ borderColor: "var(--border)" }}>
            <p className="text-xs text-center mb-3" style={{ color: "var(--muted)" }}>
              Demo accounts (click to fill):
            </p>
            <div className="grid grid-cols-1 gap-1.5">
              {[
                { email: "super.admin@vidyaverify.ai", role: "Super Admin" },
                { email: "aicte.admin@vidyaverify.ai", role: "AICTE Admin" },
                { email: "inst.admin@vidyaverify.ai", role: "Institution Admin" },
                { email: "fraud.analyst@vidyaverify.ai", role: "Fraud Analyst" },
                { email: "auditor@vidyaverify.ai", role: "Auditor" },
              ].map((acc) => (
                <button
                  key={acc.email}
                  onClick={() => fillDemo(acc.email)}
                  className="text-left px-3 py-1.5 rounded text-xs hover:bg-slate-700/50 transition-colors"
                  style={{ color: "var(--muted)" }}
                >
                  <span className="font-medium">{acc.role}</span>
                  <br />
                  <span style={{ fontSize: "11px" }}>{acc.email}</span>
                </button>
              ))}
            </div>
            <p className="text-center text-xs mt-3" style={{ color: "var(--muted)" }}>
              Password for all: Demo@2026
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
