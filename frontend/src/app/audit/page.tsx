"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";
import { formatDateTime } from "@/lib/utils";
import { ScrollText, ChevronLeft, ChevronRight } from "lucide-react";

export default function AuditPage() {
  return (
    <AppShell>
      <AuditView />
    </AppShell>
  );
}

function AuditView() {
  const [data, setData] = useState<any>(null);
  const [action, setAction] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams({ page: String(page), page_size: "50" });
    if (action) params.set("action", action);
    api.get(`/audit?${params}`).then(setData).catch(() => {}).finally(() => setLoading(false));
  }, [action, page]);

  const actions = ["login", "logout", "upload_submission", "validate_submission", "assess_risk", "transition_case", "create_user", "resolve_issue", "review_duplicate", "verification_request", "create_clarification", "respond_clarification", "override_risk_score"];

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <ScrollText size={24} /> Audit Log
        </h1>
        <p className="text-sm" style={{ color: "var(--muted)" }}>
          Append-only record of all significant operations
        </p>
      </div>

      <select value={action} onChange={(e) => { setAction(e.target.value); setPage(1); }} className="px-3 py-2 rounded-lg text-sm" style={{ background: "var(--surface)", border: "1px solid var(--border)", color: "var(--foreground)" }}>
        <option value="">All actions</option>
        {actions.map((a) => <option key={a} value={a}>{a.replace(/_/g, " ")}</option>)}
      </select>

      {loading ? (
        <div className="text-center py-8" style={{ color: "var(--muted)" }}>Loading...</div>
      ) : (
        <>
          <Card className="p-0 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left" style={{ color: "var(--muted)", borderBottom: "1px solid var(--border)" }}>
                    <th className="px-3 py-2 font-medium text-xs">Action</th>
                    <th className="px-3 py-2 font-medium text-xs">Role</th>
                    <th className="px-3 py-2 font-medium text-xs">Entity</th>
                    <th className="px-3 py-2 font-medium text-xs">Outcome</th>
                    <th className="px-3 py-2 font-medium text-xs">Reason</th>
                    <th className="px-3 py-2 font-medium text-xs">Timestamp</th>
                  </tr>
                </thead>
                <tbody>
                  {data?.items.map((l: any) => (
                    <tr key={l.id} style={{ borderBottom: "1px solid var(--border)" }}>
                      <td className="px-3 py-2 text-xs font-medium">{l.action.replace(/_/g, " ")}</td>
                      <td className="px-3 py-2 text-xs">{l.actor_role || "—"}</td>
                      <td className="px-3 py-2 text-xs">{l.entity_type || "—"} {l.entity_ref ? `(${l.entity_ref.slice(0, 8)}...)` : ""}</td>
                      <td className="px-3 py-2">
                        <span className={`badge text-xs ${l.outcome === "success" ? "text-green-600 bg-green-50" : "text-red-600 bg-red-50"}`}>{l.outcome}</span>
                      </td>
                      <td className="px-3 py-2 text-xs max-w-xs truncate" style={{ color: "var(--muted)" }}>{l.reason || "—"}</td>
                      <td className="px-3 py-2 text-xs" style={{ color: "var(--muted)" }}>{formatDateTime(l.created_at)}</td>
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
