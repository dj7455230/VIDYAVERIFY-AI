"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";
import { CheckCircle2, ChevronLeft, ChevronRight } from "lucide-react";

export default function VerificationPage() {
  return (
    <AppShell>
      <VerifView />
    </AppShell>
  );
}

function VerifView() {
  const [data, setData] = useState<any>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [provider, setProvider] = useState<any>(null);

  useEffect(() => {
    api.get("/verification/provider-status").then(setProvider).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    api.get(`/verification/requests?page=${page}&page_size=20`).then(setData).catch(() => {}).finally(() => setLoading(false));
  }, [page]);

  const statusColors: Record<string, string> = {
    matched: "text-green-600 bg-green-50 border-green-200",
    not_found: "text-gray-600 bg-gray-50 border-gray-200",
    manual_review: "text-yellow-600 bg-yellow-50 border-yellow-200",
    provider_unavailable: "text-red-600 bg-red-50 border-red-200",
    pending: "text-blue-600 bg-blue-50 border-blue-200",
  };

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <CheckCircle2 size={24} /> Verification Portal
        </h1>
        <p className="text-sm" style={{ color: "var(--muted)" }}>
          Simulated identity verification with adapter for future authorized integrations
        </p>
      </div>

      {provider && (
        <div className="p-3 rounded-lg text-xs border text-center" style={{ background: "rgba(234, 179, 8, 0.08)", borderColor: "rgba(234, 179, 8, 0.3)", color: "#eab308" }}>
          Provider: DEMO_SIMULATOR — All results are simulated, NOT real APAAR verification. No official API is connected.
        </div>
      )}

      {loading ? (
        <div className="text-center py-8" style={{ color: "var(--muted)" }}>Loading...</div>
      ) : (
        <>
          <Card className="p-0 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left" style={{ color: "var(--muted)", borderBottom: "1px solid var(--border)" }}>
                    <th className="px-4 py-3 font-medium text-xs">Reference</th>
                    <th className="px-4 py-3 font-medium text-xs">Student ID</th>
                    <th className="px-4 py-3 font-medium text-xs">Provider</th>
                    <th className="px-4 py-3 font-medium text-xs">Status</th>
                    <th className="px-4 py-3 font-medium text-xs">Completed</th>
                  </tr>
                </thead>
                <tbody>
                  {data?.items.map((r: any) => (
                    <tr key={r.id} style={{ borderBottom: "1px solid var(--border)" }}>
                      <td className="px-4 py-3 font-mono text-xs">{r.request_reference}</td>
                      <td className="px-4 py-3 font-mono text-xs">{r.student_record_id.slice(0, 8)}...</td>
                      <td className="px-4 py-3 text-xs">{r.provider_name}</td>
                      <td className="px-4 py-3">
                        <span className={`badge text-xs border capitalize ${statusColors[r.status] || ""}`}>
                          {r.status.replace(/_/g, " ")}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-xs" style={{ color: "var(--muted)" }}>
                        {r.completed_at ? new Date(r.completed_at).toLocaleString("en-IN", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }) : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
          {data && data.total_pages > 1 && (
            <div className="flex items-center justify-between">
              <span className="text-xs" style={{ color: "var(--muted)" }}>Page {data.page} of {data.total_pages} ({data.total} total)</span>
              <div className="flex gap-1">
                <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="p-1.5 rounded disabled:opacity-30" style={{ background: "var(--surface)" }}><ChevronLeft size={16} /></button>
                <button onClick={() => setPage(p => p + 1)} disabled={page >= (data?.total_pages || 1)} className="p-1.5 rounded disabled:opacity-30" style={{ background: "var(--surface)" }}><ChevronRight size={16} /></button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
