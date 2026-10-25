"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";
import { formatDate, formatDateTime } from "@/lib/utils";
import { ArrowLeft } from "lucide-react";

export default function RiskDetailPage() {
  return (
    <AppShell>
      <RiskDetail />
    </AppShell>
  );
}

function RiskDetail() {
  const params = useParams();
  const id = params.id as string;
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [overrideScore, setOverrideScore] = useState("");
  const [overrideJust, setOverrideJust] = useState("");
  const [overrideMsg, setOverrideMsg] = useState("");

  useEffect(() => {
    api.get(`/risk/cases/${id}`).then(setData).catch(() => {}).finally(() => setLoading(false));
  }, [id]);

  const submitOverride = async () => {
    if (!overrideJust.trim()) { setOverrideMsg("Justification is required"); return; }
    try {
      await api.post(`/risk/cases/${id}/override`, {
        new_score: parseFloat(overrideScore) || 0,
        justification: overrideJust,
      });
      setOverrideMsg("Risk score overridden. Audit recorded.");
      setOverrideJust("");
      setOverrideScore("");
      api.get(`/risk/cases/${id}`).then(setData);
    } catch (e: any) { setOverrideMsg(e.message); }
  };

  if (loading) return <div className="text-center py-8" style={{ color: "var(--muted)" }}>Loading...</div>;
  if (!data) return <Card><p>Case not found</p></Card>;

  return (
    <div className="space-y-4">
      <a href="/risk" className="flex items-center gap-1 text-sm hover:text-cyan-400" style={{ color: "var(--muted)" }}>
        <ArrowLeft size={14} /> Back to Risk Cases
      </a>
      <div>
        <p className="font-mono text-xs" style={{ color: "var(--muted)" }}>{data.case_number}</p>
        <h1 className="text-2xl font-bold">{data.title}</h1>
        <p className="text-sm" style={{ color: "var(--muted)" }}>{data.demo_label}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card>
          <h3 className="text-sm font-semibold mb-3">Risk Score</h3>
          <div className="text-center py-4">
            <div className="text-5xl font-bold mb-2">{data.risk_score}</div>
            <span className={`badge text-xs border capitalize px-3 py-1 ${
              data.risk_band === "critical" ? "text-red-600 bg-red-50 border-red-200" :
              data.risk_band === "high" ? "text-orange-600 bg-orange-50 border-orange-200" :
              data.risk_band === "medium" ? "text-yellow-600 bg-yellow-50 border-yellow-200" :
              "text-green-600 bg-green-50 border-green-200"
            }`}>{data.risk_band}</span>
          </div>
          <p className="text-xs text-center mt-3" style={{ color: "var(--muted)" }}>
            {data.explanation}
          </p>
          <p className="text-xs text-center mt-2" style={{ color: "var(--muted)" }}>
            Risk version: {data.risk_version}
          </p>
        </Card>

        <Card className="lg:col-span-2">
          <h3 className="text-sm font-semibold mb-3">Contributing Factors</h3>
          {data.factors.length === 0 ? (
            <p className="text-sm" style={{ color: "var(--muted)" }}>No active risk factors.</p>
          ) : (
            <div className="space-y-3">
              {data.factors.map((f: any) => (
                <div key={f.id} className="flex items-start gap-3 p-3 rounded-lg" style={{ background: "var(--background)" }}>
                  <div className="text-center shrink-0">
                    <div className="text-lg font-bold text-orange-400">+{f.weight}</div>
                    <div className="text-xs" style={{ color: "var(--muted)" }}>points</div>
                  </div>
                  <div className="min-w-0">
                    <p className="font-mono text-xs" style={{ color: "var(--muted)" }}>{f.rule_code}</p>
                    <p className="text-sm">{f.description}</p>
                    {f.evidence_ref && (
                      <p className="text-xs mt-1" style={{ color: "var(--muted)" }}>
                        Evidence: {JSON.stringify(f.evidence_ref)}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      <Card>
        <h3 className="text-sm font-semibold mb-3">Score History</h3>
        {data.score_history.length === 0 ? (
          <p className="text-sm" style={{ color: "var(--muted)" }}>No history available.</p>
        ) : (
          <div className="space-y-2">
            {data.score_history.map((h: any) => (
              <div key={h.id} className="flex items-center justify-between p-2 rounded-lg" style={{ background: "var(--background)" }}>
                <div>
                  <span className="text-sm">
                    {h.previous_score !== null ? `${h.previous_score} → ${h.new_score}` : `${h.new_score} (initial)`}
                  </span>
                  <span className={`badge text-xs border ml-2 capitalize ${
                    h.new_band === "critical" ? "text-red-600 bg-red-50 border-red-200" :
                    h.new_band === "high" ? "text-orange-600 bg-orange-50 border-orange-200" :
                    h.new_band === "medium" ? "text-yellow-600 bg-yellow-50 border-yellow-200" :
                    "text-green-600 bg-green-50 border-green-200"
                  }`}>{h.new_band}</span>
                </div>
                <div className="text-right">
                  <p className="text-xs" style={{ color: "var(--muted)" }}>{h.change_reason}</p>
                  <p className="text-xs" style={{ color: "var(--muted)" }}>{formatDateTime(h.created_at)}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      <Card>
        <h3 className="text-sm font-semibold mb-3">Override Risk Score (requires justification)</h3>
        <div className="space-y-3">
          <div className="flex gap-3">
            <input
              type="number"
              min="0"
              max="100"
              value={overrideScore}
              onChange={(e) => setOverrideScore(e.target.value)}
              placeholder="New score (0-100)"
              className="px-3 py-2 rounded-lg text-sm w-40"
              style={{ background: "var(--background)", border: "1px solid var(--border)", color: "var(--foreground)" }}
            />
            <input
              type="text"
              value={overrideJust}
              onChange={(e) => setOverrideJust(e.target.value)}
              placeholder="Mandatory justification for override..."
              className="flex-1 px-3 py-2 rounded-lg text-sm"
              style={{ background: "var(--background)", border: "1px solid var(--border)", color: "var(--foreground)" }}
            />
            <button onClick={submitOverride} className="px-4 py-2 rounded-lg text-sm font-medium text-white" style={{ background: "var(--accent)" }}>
              Override
            </button>
          </div>
          {overrideMsg && <p className="text-xs" style={{ color: overrideMsg.includes("required") || overrideMsg.includes("Error") ? "#ef4444" : "#22c55e" }}>{overrideMsg}</p>}
        </div>
      </Card>
    </div>
  );
}
