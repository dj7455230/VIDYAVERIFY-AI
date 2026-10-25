"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";
import { ShieldAlert, ChevronLeft, ChevronRight } from "lucide-react";

export default function DuplicatesPage() {
  return (
    <AppShell>
      <DupView />
    </AppShell>
  );
}

function DupView() {
  const [data, setData] = useState<any>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [crossOnly, setCrossOnly] = useState(false);

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams({ page: String(page), page_size: "20" });
    if (crossOnly) params.set("cross_institution_only", "true");
    api.get(`/duplicates?${params}`).then(setData).catch(() => {}).finally(() => setLoading(false));
  }, [page, crossOnly]);

  const review = async (id: string, decision: string) => {
    try {
      await api.post(`/duplicates/${id}/review`, { decision });
      const params = new URLSearchParams({ page: String(page), page_size: "20" });
      if (crossOnly) params.set("cross_institution_only", "true");
      api.get(`/duplicates?${params}`).then(setData);
    } catch {}
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <ShieldAlert size={24} /> Potential Duplicates
          </h1>
          <p className="text-sm" style={{ color: "var(--muted)" }}>
            Layered detection — records are NOT merged automatically. Similar names alone are not proof of wrongdoing.
          </p>
        </div>
        <button
          onClick={() => setCrossOnly(!crossOnly)}
          className="px-3 py-1.5 rounded-lg text-xs font-medium"
          style={crossOnly ? { background: "var(--accent)", color: "white" } : { background: "var(--surface)", color: "var(--muted)" }}
        >
          {crossOnly ? "Showing cross-institution only" : "Show cross-institution only"}
        </button>
      </div>

      {loading ? (
        <div className="text-center py-8" style={{ color: "var(--muted)" }}>Loading...</div>
      ) : (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
            {data?.items.map((c: any) => (
              <Card key={c.id}>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="badge text-xs border text-blue-600 bg-blue-50 border-blue-200">Layer {c.match_layer}</span>
                    {c.is_cross_institution && <span className="badge text-xs border text-red-600 bg-red-50 border-red-200">Cross-institution</span>}
                  </div>
                  <div className="text-2xl font-bold tabular-nums">{c.match_score.toFixed(0)}%</div>
                </div>
                <div className="grid grid-cols-2 gap-2 mb-3">
                  <div className="p-2 rounded-lg" style={{ background: "var(--background)" }}>
                    <p className="text-xs font-medium">{c.student_1.name}</p>
                    <p className="text-xs font-mono" style={{ color: "var(--muted)" }}>{c.student_1.apaar_masked}</p>
                    <p className="text-xs" style={{ color: "var(--muted)" }}>{c.student_1.institution_name}</p>
                  </div>
                  <div className="p-2 rounded-lg" style={{ background: "var(--background)" }}>
                    <p className="text-xs font-medium">{c.student_2.name}</p>
                    <p className="text-xs font-mono" style={{ color: "var(--muted)" }}>{c.student_2.apaar_masked}</p>
                    <p className="text-xs" style={{ color: "var(--muted)" }}>{c.student_2.institution_name}</p>
                  </div>
                </div>
                <p className="text-xs mb-2" style={{ color: "var(--muted)" }}>{c.match_explanation}</p>
                <div className="flex items-center justify-between">
                  <span className={`badge text-xs border capitalize ${
                    c.reviewer_decision === "confirmed_duplicate" ? "text-red-600 bg-red-50 border-red-200" :
                    c.reviewer_decision === "not_duplicate" ? "text-green-600 bg-green-50 border-green-200" :
                    "text-yellow-600 bg-yellow-50 border-yellow-200"
                  }`}>
                    {c.reviewer_decision.replace(/_/g, " ")}
                  </span>
                  {c.reviewer_decision === "unresolved" && (
                    <div className="flex gap-1">
                      <button onClick={() => review(c.id, "confirmed_duplicate")} className="px-2 py-1 rounded text-xs text-red-400 hover:bg-red-500/10">Confirm Dup</button>
                      <button onClick={() => review(c.id, "not_duplicate")} className="px-2 py-1 rounded text-xs text-green-400 hover:bg-green-500/10">Not Dup</button>
                      <button onClick={() => review(c.id, "needs_review")} className="px-2 py-1 rounded text-xs text-yellow-400 hover:bg-yellow-500/10">Needs Review</button>
                    </div>
                  )}
                </div>
              </Card>
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
