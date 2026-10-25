"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { Card, MetricCard, StatusBadge } from "@/components/ui/Card";
import { api } from "@/lib/api";
import {
  CheckSquare,
  AlertTriangle,
  FileSpreadsheet,
  CheckCircle2,
  XCircle,
  Filter,
  Download,
  ArrowRight,
  ShieldAlert,
  Building,
} from "lucide-react";
import Link from "next/link";

interface Issue {
  id: string;
  issue_code: string;
  severity: "critical" | "error" | "warning" | "info";
  field_name: string;
  row_number: number;
  explanation: string;
  expected_value: string;
  observed_value: string;
  recommended_action: string;
  status: string;
  resolved_at: string | null;
  resolution_note: string | null;
}

export default function ValidationPage() {
  return (
    <AppShell>
      <ValidationView />
    </AppShell>
  );
}

function ValidationView() {
  const [batches, setBatches] = useState<any[]>([]);
  const [selectedBatchId, setSelectedBatchId] = useState<string>("");
  const [issues, setIssues] = useState<Issue[]>([]);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [reconciliations, setReconciliations] = useState<any[]>([]);
  const [resolvingId, setResolvingId] = useState<string | null>(null);
  const [resolutionNote, setResolutionNote] = useState<string>("");
  const [actionSuccess, setActionSuccess] = useState<string>("");

  useEffect(() => {
    // Fetch recent batches and reconciliation summary
    Promise.all([
      api.get<any>("/submissions?page=1&page_size=20").catch(() => ({ items: [] })),
      api.get<any>("/dashboard/metrics").catch(() => null),
    ]).then(([subs, dash]) => {
      if (subs?.items?.length) {
        setBatches(subs.items);
        setSelectedBatchId(subs.items[0].id);
      }
      if (dash?.intake_reconciliation) {
        setReconciliations(dash.intake_reconciliation);
      }
    }).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedBatchId) return;
    setLoading(true);
    const params = new URLSearchParams({ page: "1", page_size: "100" });
    if (severityFilter !== "all") params.set("severity", severityFilter);
    if (statusFilter !== "all") params.set("status", statusFilter);

    api.get<any>(`/submissions/${selectedBatchId}/issues?${params}`)
      .then((res) => {
        setIssues(res.items || []);
      })
      .catch(() => setIssues([]))
      .finally(() => setLoading(false));
  }, [selectedBatchId, severityFilter, statusFilter]);

  const handleResolveIssue = async (issueId: string, status: "resolved" | "accepted_justified") => {
    try {
      await api.post(`/submissions/${selectedBatchId}/issues/${issueId}/resolve`, {
        status,
        note: resolutionNote || "Verified by institutional compliance officer.",
      });
      setActionSuccess(`Issue marked as ${status.replace("_", " ")}`);
      setResolvingId(null);
      setResolutionNote("");
      // Refresh issues
      const res = await api.get<any>(`/submissions/${selectedBatchId}/issues?page=1&page_size=100`);
      setIssues(res.items || []);
      setTimeout(() => setActionSuccess(""), 4000);
    } catch (err: any) {
      alert(err.message || "Failed to resolve issue");
    }
  };

  const selectedBatch = batches.find((b) => b.id === selectedBatchId);
  const criticalCount = issues.filter((i) => i.severity === "critical").length;
  const errorCount = issues.filter((i) => i.severity === "error").length;
  const warningCount = issues.filter((i) => i.severity === "warning").length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2.5">
            <CheckSquare className="text-cyan-400" size={26} /> Validation & Reconciliation Engine
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Deterministic rule engine for intake limits, required fields, formats, and APAAR duplicate checks.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href="/upload"
            className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition-colors flex items-center gap-1.5 shadow-sm"
          >
            <FileSpreadsheet size={15} /> Upload New Batch
          </Link>
        </div>
      </div>

      {actionSuccess && (
        <div className="p-3 rounded-lg border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 text-xs flex items-center gap-2">
          <CheckCircle2 size={16} /> {actionSuccess}
        </div>
      )}

      {/* Batch selector and metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <Card className="lg:col-span-1 flex flex-col justify-between">
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Select Submission Batch
            </label>
            <select
              value={selectedBatchId}
              onChange={(e) => setSelectedBatchId(e.target.value)}
              className="w-full px-3 py-2 rounded-lg text-xs bg-slate-900 border border-slate-700 text-slate-200 focus:outline-none focus:border-cyan-500"
            >
              {batches.map((b) => (
                <option key={b.id} value={b.id}>
                  Batch {b.id.slice(0, 8)} • {b.institution_name || "Inst"} ({b.total_rows} rows)
                </option>
              ))}
            </select>
            {selectedBatch && (
              <div className="mt-3 space-y-1.5 text-xs text-slate-400 pt-3 border-t border-slate-800">
                <p className="flex justify-between">
                  <span>Batch Status:</span>
                  <span className="font-semibold text-slate-200 capitalize">{selectedBatch.status}</span>
                </p>
                <p className="flex justify-between">
                  <span>Total Ingested:</span>
                  <span className="font-semibold text-slate-200">{selectedBatch.total_rows} records</span>
                </p>
                <p className="flex justify-between">
                  <span>Valid Rows:</span>
                  <span className="font-semibold text-emerald-400">{selectedBatch.valid_rows || 0}</span>
                </p>
                <p className="flex justify-between">
                  <span>Invalid Rows:</span>
                  <span className="font-semibold text-rose-400">{selectedBatch.invalid_rows || 0}</span>
                </p>
              </div>
            )}
          </div>
        </Card>

        <MetricCard
          label="Critical Violations"
          value={criticalCount}
          icon={AlertTriangle}
          color="#ef4444"
          trend="Immediate review"
        />
        <MetricCard
          label="Validation Errors"
          value={errorCount}
          icon={XCircle}
          color="#f97316"
          trend="Action required"
        />
        <MetricCard
          label="Format Warnings"
          value={warningCount}
          icon={CheckSquare}
          color="#eab308"
          trend="Review permitted"
        />
      </div>

      {/* Intake Reconciliation Overview */}
      <Card>
        <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Building size={18} className="text-cyan-400" />
            <h3 className="font-bold text-sm text-slate-200">AICTE Approved Intake vs. Submitted Enrolment</h3>
          </div>
          <span className="text-[11px] font-mono text-slate-400">Section 10(k) Compliance Check</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left text-slate-400 border-b border-slate-800">
                <th className="pb-2 font-semibold">Institution Name</th>
                <th className="pb-2 font-semibold">Course Program</th>
                <th className="pb-2 font-semibold text-right">AICTE Approved Capacity</th>
                <th className="pb-2 font-semibold text-right">Submitted Enrolment</th>
                <th className="pb-2 font-semibold text-right">Discrepancy</th>
                <th className="pb-2 font-semibold text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {reconciliations.slice(0, 5).map((r, i) => {
                const diff = r.actual_enrolment - r.approved_intake;
                return (
                  <tr key={i} className="table-row-hover">
                    <td className="py-2.5 font-medium text-slate-200">{r.institution_name}</td>
                    <td className="py-2.5 text-slate-300">{r.course_name}</td>
                    <td className="py-2.5 text-right font-mono text-slate-300">{r.approved_intake}</td>
                    <td className="py-2.5 text-right font-mono font-semibold text-slate-100">{r.actual_enrolment}</td>
                    <td className="py-2.5 text-right font-mono font-semibold">
                      {diff > 0 ? (
                        <span className="text-rose-400">+{diff} (Over-intake)</span>
                      ) : (
                        <span className="text-emerald-400">{diff}</span>
                      )}
                    </td>
                    <td className="py-2.5 text-right">
                      <StatusBadge status={r.status} />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Issue Explorer & Resolution */}
      <Card>
        <div className="flex items-center justify-between flex-wrap gap-3 mb-4">
          <div className="flex items-center gap-2">
            <ShieldAlert size={18} className="text-amber-400" />
            <h3 className="font-bold text-sm text-slate-200">
              Row-Level Validation Issues ({issues.length})
            </h3>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1 text-xs">
              <Filter size={13} className="text-slate-400" />
              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
                className="bg-transparent text-slate-200 focus:outline-none"
              >
                <option value="all">All Severities</option>
                <option value="critical">Critical</option>
                <option value="error">Error</option>
                <option value="warning">Warning</option>
              </select>
            </div>
            <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1 text-xs">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="bg-transparent text-slate-200 focus:outline-none"
              >
                <option value="all">All Statuses</option>
                <option value="open">Open</option>
                <option value="resolved">Resolved</option>
                <option value="accepted_justified">Accepted Justified</option>
              </select>
            </div>
          </div>
        </div>

        {issues.length === 0 ? (
          <div className="text-center py-10 text-slate-500 text-xs">
            No validation issues matching current criteria. All student rows verified compliant.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-left text-slate-400 border-b border-slate-800">
                  <th className="pb-2 font-semibold">Row</th>
                  <th className="pb-2 font-semibold">Severity</th>
                  <th className="pb-2 font-semibold">Issue Code</th>
                  <th className="pb-2 font-semibold">Field</th>
                  <th className="pb-2 font-semibold">Explanation & Evidence</th>
                  <th className="pb-2 font-semibold">Status</th>
                  <th className="pb-2 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {issues.map((issue) => (
                  <tr key={issue.id} className="table-row-hover">
                    <td className="py-3 font-mono text-slate-400">#{issue.row_number}</td>
                    <td className="py-3">
                      <StatusBadge status={issue.severity} />
                    </td>
                    <td className="py-3 font-mono font-medium text-slate-200">{issue.issue_code}</td>
                    <td className="py-3 font-mono text-cyan-400">{issue.field_name}</td>
                    <td className="py-3 max-w-md">
                      <p className="text-slate-200">{issue.explanation}</p>
                      {issue.observed_value && (
                        <p className="text-[11px] text-slate-400 mt-0.5">
                          Observed: <span className="font-mono text-slate-300">{issue.observed_value}</span>
                          {issue.expected_value && (
                            <> • Expected: <span className="font-mono text-emerald-400">{issue.expected_value}</span></>
                          )}
                        </p>
                      )}
                      <p className="text-[10px] text-cyan-400/80 mt-0.5 font-medium">
                        Action: {issue.recommended_action}
                      </p>
                    </td>
                    <td className="py-3">
                      <StatusBadge status={issue.status} />
                    </td>
                    <td className="py-3 text-right">
                      {issue.status === "open" ? (
                        <button
                          onClick={() => setResolvingId(resolvingId === issue.id ? null : issue.id)}
                          className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium transition-colors"
                        >
                          Resolve
                        </button>
                      ) : (
                        <span className="text-[11px] text-slate-500 font-mono">
                          {issue.resolved_at ? new Date(issue.resolved_at).toLocaleDateString() : "Resolved"}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Modal/Inline Resolution Form */}
        {resolvingId && (
          <div className="mt-4 p-4 rounded-xl border border-cyan-500/30 bg-slate-900/90 space-y-3">
            <h4 className="text-xs font-bold text-cyan-400 uppercase tracking-wider">
              Resolve Validation Issue #{issues.find((i) => i.id === resolvingId)?.row_number}
            </h4>
            <input
              type="text"
              placeholder="Enter institutional justification or correction rationale..."
              value={resolutionNote}
              onChange={(e) => setResolutionNote(e.target.value)}
              className="w-full px-3 py-2 rounded-lg text-xs bg-slate-950 border border-slate-700 text-slate-200 focus:outline-none focus:border-cyan-400"
            />
            <div className="flex items-center gap-2 justify-end">
              <button
                onClick={() => setResolvingId(null)}
                className="px-3 py-1.5 rounded-lg text-xs text-slate-400 hover:text-slate-200"
              >
                Cancel
              </button>
              <button
                onClick={() => handleResolveIssue(resolvingId, "accepted_justified")}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-500 hover:bg-indigo-400 text-slate-950"
              >
                Accept with Justification
              </button>
              <button
                onClick={() => handleResolveIssue(resolvingId, "resolved")}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-500 hover:bg-emerald-400 text-slate-950"
              >
                Confirm Correction & Resolve
              </button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
