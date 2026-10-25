"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";
import { type RiskCase, type PaginatedResponse, RISK_BAND_COLORS } from "@/types";
import { ShieldAlert, ChevronLeft, ChevronRight } from "lucide-react";

export default function RiskPage() {
  return (
    <AppShell>
      <RiskView />
    </AppShell>
  );
}

function RiskView() {
  const [data, setData] = useState<PaginatedResponse<RiskCase> | null>(null);
  const [band, setBand] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams({ page: String(page), page_size: "20" });
    if (band) params.set("risk_band", band);
    api
      .get<PaginatedResponse<RiskCase>>(`/risk/cases?${params}`)
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [band, page]);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <ShieldAlert size={24} /> Risk Cases
        </h1>
        <p className="text-sm" style={{ color: "var(--muted)" }}>
          Explainable risk scoring — scores are illustrative prototype weights, not validated policy
        </p>
      </div>

      <div className="flex gap-2 flex-wrap">
        {["", "low", "medium", "high", "critical"].map((b) => (
          <button
            key={b}
            onClick={() => { setBand(b); setPage(1); }}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${band === b ? "text-white" : ""}`}
            style={band === b ? { background: "var(--accent)" } : { background: "var(--surface)", color: "var(--muted)" }}
          >
            {b || "All Bands"}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-center py-8" style={{ color: "var(--muted)" }}>Loading...</div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {data?.items.map((c) => (
              <a key={c.id} href={`/risk/${c.id}`}>
                <Card className="hover:border-cyan-500/50 transition-colors">
                  <div className="flex items-start justify-between mb-2">
                    <div className="min-w-0">
                      <p className="font-mono text-xs" style={{ color: "var(--muted)" }}>{c.case_number}</p>
                      <p className="font-medium text-sm truncate">{c.title}</p>
                    </div>
                    <span className={`badge text-xs border ${RISK_BAND_COLORS[c.risk_band] || ""} capitalize shrink-0 ml-2`}>
                      {c.risk_band}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 mt-3">
                    <div className="flex-1">
                      <div className="h-2 rounded-full overflow-hidden" style={{ background: "var(--background)" }}>
                        <div
                          className="h-full rounded-full"
                          style={{
                            width: `${c.risk_score}%`,
                            background:
                              c.risk_band === "critical" ? "#ef4444" :
                              c.risk_band === "high" ? "#f97316" :
                              c.risk_band === "medium" ? "#eab308" : "#22c55e",
                          }}
                        />
                      </div>
                    </div>
                    <span className="text-lg font-bold tabular-nums">{c.risk_score}</span>
                  </div>
                  <p className="text-xs mt-2" style={{ color: "var(--muted)" }}>
                    Status: <span className="capitalize">{c.status.replace(/_/g, " ")}</span>
                  </p>
                </Card>
              </a>
            ))}
          </div>
          {data && data.total_pages > 1 && (
            <div className="flex items-center justify-between">
              <span className="text-xs" style={{ color: "var(--muted)" }}>
                Page {data.page} of {data.total_pages} ({data.total} total)
              </span>
              <div className="flex gap-1">
                <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="p-1.5 rounded disabled:opacity-30" style={{ background: "var(--surface)" }}>
                  <ChevronLeft size={16} />
                </button>
                <button onClick={() => setPage(p => p + 1)} disabled={page >= (data?.total_pages || 1)} className="p-1.5 rounded disabled:opacity-30" style={{ background: "var(--surface)" }}>
                  <ChevronRight size={16} />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
