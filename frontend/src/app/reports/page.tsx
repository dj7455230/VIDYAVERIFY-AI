"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";
import { FileBarChart, Download } from "lucide-react";

export default function ReportsPage() {
  return (
    <AppShell>
      <ReportsView />
    </AppShell>
  );
}

function ReportsView() {
  const [report, setReport] = useState<any>(null);
  const [reportType, setReportType] = useState("institution-summary");

  const reports = [
    { key: "institution-summary", label: "Institution Summary" },
    { key: "intake-reconciliation", label: "Intake Reconciliation" },
    { key: "validation-issues", label: "Validation Issues" },
    { key: "risk-cases", label: "Risk Case Register" },
    { key: "audit", label: "Audit Report" },
  ];

  useEffect(() => {
    api.get(`/reports/${reportType}`).then(setReport).catch(() => {});
  }, [reportType]);

  const download = () => {
    const token = typeof window !== "undefined" ? localStorage.getItem("vv_token") : "";
    const tokenParam = token ? `&token=${encodeURIComponent(token)}` : "";
    window.open(`http://127.0.0.1:8000/api/v1/reports/${reportType}?export=csv${tokenParam}`, "_blank");
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <FileBarChart size={24} /> Reports
          </h1>
          <p className="text-sm" style={{ color: "var(--muted)" }}>
            Database-backed reports with CSV export
          </p>
        </div>
        <button onClick={download} className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-white" style={{ background: "var(--accent)" }}>
          <Download size={16} /> Export CSV
        </button>
      </div>

      <div className="flex gap-2 flex-wrap">
        {reports.map((r) => (
          <button
            key={r.key}
            onClick={() => setReportType(r.key)}
            className="px-3 py-1.5 rounded-lg text-xs font-medium"
            style={reportType === r.key ? { background: "var(--accent)", color: "white" } : { background: "var(--surface)", color: "var(--muted)" }}
          >
            {r.label}
          </button>
        ))}
      </div>

      {report && (
        <Card className="p-0 overflow-hidden">
          {report.items.length === 0 ? (
            <p className="text-center py-8" style={{ color: "var(--muted)" }}>No data available</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left" style={{ color: "var(--muted)", borderBottom: "1px solid var(--border)" }}>
                    {Object.keys(report.items[0]).map((k) => (
                      <th key={k} className="px-3 py-2 font-medium text-xs capitalize">{k.replace(/_/g, " ")}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {report.items.map((item: any, i: number) => (
                    <tr key={i} style={{ borderBottom: "1px solid var(--border)" }}>
                      {Object.values(item).map((v: any, j: number) => (
                        <td key={j} className="px-3 py-2 text-xs">{String(v).slice(0, 50)}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <div className="p-3 text-xs border-t" style={{ borderColor: "var(--border)", color: "var(--muted)" }}>
            {report.total} records · {report.demo_label || ""}
          </div>
        </Card>
      )}
    </div>
  );
}
