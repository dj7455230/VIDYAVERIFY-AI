"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";
import { formatDateTime } from "@/lib/utils";
import { ArrowLeft } from "lucide-react";

export default function CaseDetailPage() {
  return (
    <AppShell>
      <CaseDetail />
    </AppShell>
  );
}

function CaseDetail() {
  const params = useParams();
  const id = params.id as string;
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [newStatus, setNewStatus] = useState("");
  const [reason, setReason] = useState("");
  const [note, setNote] = useState("");
  const [msg, setMsg] = useState("");

  useEffect(() => {
    api.get(`/cases/${id}`).then(setData).catch(() => {}).finally(() => setLoading(false));
  }, [id]);

  const transition = async () => {
    if (!newStatus) { setMsg("Select a new status"); return; }
    try {
      await api.post(`/cases/${id}/transition`, { new_status: newStatus, reason, note });
      setMsg("Case transitioned. Audit recorded.");
      setReason(""); setNote(""); setNewStatus("");
      api.get(`/cases/${id}`).then(setData);
    } catch (e: any) { setMsg(e.message); }
  };

  if (loading) return <div className="text-center py-8" style={{ color: "var(--muted)" }}>Loading...</div>;
  if (!data) return <Card><p>Case not found</p></Card>;

  return (
    <div className="space-y-4">
      <a href="/cases" className="flex items-center gap-1 text-sm hover:text-cyan-400" style={{ color: "var(--muted)" }}>
        <ArrowLeft size={14} /> Back to Cases
      </a>
      <div>
        <p className="font-mono text-xs" style={{ color: "var(--muted)" }}>{data.case_number}</p>
        <h1 className="text-2xl font-bold">{data.title}</h1>
        <p className="text-sm" style={{ color: "var(--muted)" }}>{data.description}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <h3 className="text-sm font-semibold mb-3">Evidence</h3>
          {data.evidence.length === 0 ? (
            <p className="text-sm" style={{ color: "var(--muted)" }}>No evidence items.</p>
          ) : (
            <div className="space-y-2">
              {data.evidence.map((e: any) => (
                <div key={e.id} className="p-2 rounded-lg" style={{ background: "var(--background)" }}>
                  <p className="text-xs font-medium">{e.evidence_type.replace(/_/g, " ")}</p>
                  <p className="text-xs">{e.description}</p>
                  <p className="text-xs" style={{ color: "var(--muted)" }}>{formatDateTime(e.created_at)}</p>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card>
          <h3 className="text-sm font-semibold mb-3">Action History (Audit Trail)</h3>
          {data.action_history.length === 0 ? (
            <p className="text-sm" style={{ color: "var(--muted)" }}>No actions recorded.</p>
          ) : (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {data.action_history.map((a: any) => (
                <div key={a.id} className="p-2 rounded-lg" style={{ background: "var(--background)" }}>
                  <p className="text-xs font-medium">{a.action_type.replace(/_/g, " ")}</p>
                  {a.previous_status && <p className="text-xs" style={{ color: "var(--muted)" }}>{a.previous_status} → {a.new_status}</p>}
                  {a.note && <p className="text-xs">{a.note}</p>}
                  <p className="text-xs" style={{ color: "var(--muted)" }}>{formatDateTime(a.created_at)}</p>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      <Card>
        <h3 className="text-sm font-semibold mb-3">Transition Case</h3>
        <div className="grid grid-cols-3 gap-3">
          <select value={newStatus} onChange={(e) => setNewStatus(e.target.value)} className="px-3 py-2 rounded-lg text-sm" style={{ background: "var(--background)", border: "1px solid var(--border)", color: "var(--foreground)" }}>
            <option value="">Select status...</option>
            <option value="open">Open</option>
            <option value="assigned">Assigned</option>
            <option value="under_review">Under Review</option>
            <option value="awaiting_institution_response">Awaiting Institution Response</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
          </select>
          <input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Reason (required for resolve)" className="px-3 py-2 rounded-lg text-sm" style={{ background: "var(--background)", border: "1px solid var(--border)", color: "var(--foreground)" }} />
          <input value={note} onChange={(e) => setNote(e.target.value)} placeholder="Note (optional)" className="px-3 py-2 rounded-lg text-sm" style={{ background: "var(--background)", border: "1px solid var(--border)", color: "var(--foreground)" }} />
        </div>
        <button onClick={transition} className="mt-3 px-4 py-2 rounded-lg text-sm text-white" style={{ background: "var(--accent)" }}>
          Transition Case
        </button>
        {msg && <p className="text-xs mt-2" style={{ color: msg.includes("error") || msg.includes("Select") ? "#ef4444" : "#22c55e" }}>{msg}</p>}
      </Card>
    </div>
  );
}
