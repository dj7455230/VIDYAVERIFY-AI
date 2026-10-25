"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";
import { type PaginatedResponse, STATUS_COLORS } from "@/types";
import { FolderSearch, ChevronLeft, ChevronRight } from "lucide-react";

export default function CasesPage() {
  return (
    <AppShell>
      <CasesView />
    </AppShell>
  );
}

function CasesView() {
  const [data, setData] = useState<PaginatedResponse<any> | null>(null);
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams({ page: String(page), page_size: "20" });
    if (status) params.set("status", status);
    api.get<PaginatedResponse<any>>(`/cases?${params}`).then(setData).catch(() => {}).finally(() => setLoading(false));
  }, [status, page]);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <FolderSearch size={24} /> Investigation Cases
        </h1>
        <p className="text-sm" style={{ color: "var(--muted)" }}>Case management with full audit trail</p>
      </div>
      <div className="flex gap-2 flex-wrap">
        {["", "open", "assigned", "under_review", "awaiting_institution_response", "resolved", "closed"].map((s) => (
          <button
            key={s}
            onClick={() => { setStatus(s); setPage(1); }}
            className="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors"
            style={status === s ? { background: "var(--accent)", color: "white" } : { background: "var(--surface)", color: "var(--muted)" }}
          >
            {s ? s.replace(/_/g, " ") : "All"}
          </button>
        ))}
      </div>
      {loading ? (
        <div className="text-center py-8" style={{ color: "var(--muted)" }}>Loading...</div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {data?.items.map((c) => (
              <a key={c.id} href={`/cases/${c.id}`}>
                <Card className="hover:border-cyan-500/50 transition-colors">
                  <div className="flex items-start justify-between mb-2">
                    <div className="min-w-0">
                      <p className="font-mono text-xs" style={{ color: "var(--muted)" }}>{c.case_number}</p>
                      <p className="font-medium text-sm">{c.title}</p>
                    </div>
                    <span className={`badge text-xs border ${STATUS_COLORS[c.status] || "text-gray-600 bg-gray-50"} capitalize shrink-0 ml-2`}>
                      {c.status.replace(/_/g, " ")}
                    </span>
                  </div>
                  <p className="text-xs mt-2" style={{ color: "var(--muted)" }}>
                    Severity: <span className={`font-medium capitalize ${c.severity === "critical" ? "text-red-400" : c.severity === "high" ? "text-orange-400" : ""}`}>{c.severity}</span>
                  </p>
                </Card>
              </a>
            ))}
          </div>
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
