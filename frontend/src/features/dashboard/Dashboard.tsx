"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import {
  Building2,
  CheckCircle2,
  GraduationCap,
  Upload,
  AlertTriangle,
  FolderSearch,
  CheckSquare,
  ShieldAlert,
  ArrowUpRight,
  TrendingUp,
  Activity,
  Layers,
  Sparkles,
  FileSpreadsheet,
} from "lucide-react";
import { Card, MetricCard, StatusBadge } from "@/components/ui/Card";
import { formatDate } from "@/lib/utils";
import {
  type DashboardData,
} from "@/types";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import Link from "next/link";

export function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get<DashboardData>("/dashboard/metrics")
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading)
    return (
      <div className="flex flex-col items-center justify-center h-80 space-y-3">
        <div
          className="w-10 h-10 border-2 rounded-full animate-spin"
          style={{
            borderColor: "var(--accent)",
            borderTopColor: "transparent",
          }}
        />
        <p className="text-xs text-slate-400">Loading AICTE Institutional Metrics...</p>
      </div>
    );

  if (error)
    return (
      <Card>
        <p className="text-rose-400 text-sm">Failed to connect to backend: {error}</p>
      </Card>
    );

  if (!data) return null;

  const riskData = [
    { band: "Low (0-30)", count: data.cases_by_risk.low, fill: "#10b981" },
    { band: "Medium (31-60)", count: data.cases_by_risk.medium, fill: "#f59e0b" },
    { band: "High (61-80)", count: data.cases_by_risk.high, fill: "#f97316" },
    { band: "Critical (81-100)", count: data.cases_by_risk.critical, fill: "#ef4444" },
  ];

  return (
    <div className="space-y-6">
      {/* Top Banner / Hero */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-slate-100">AICTE Command Centre</h1>
            <span
              className="text-[10px] font-mono px-2 py-0.5 rounded-full border border-cyan-500/40 bg-cyan-500/10 text-cyan-400 font-semibold uppercase tracking-wider"
            >
              PROD-READY PROTO v2.0
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            APAAR ID Student Data Management & Verification Platform for AICTE-Approved Institutions (SIH26263)
          </p>
        </div>

        {/* Quick Actions */}
        <div className="flex items-center gap-2">
          <Link
            href="/upload"
            className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition-colors flex items-center gap-1.5 shadow-sm"
          >
            <Upload size={14} /> Upload Records
          </Link>
          <Link
            href="/copilot"
            className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors flex items-center gap-1.5"
          >
            <Sparkles size={14} className="text-cyan-400" /> Copilot
          </Link>
        </div>
      </div>

      {/* 6 Key Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5">
        <MetricCard
          label="Institutions"
          value={data.metrics.total_institutions}
          icon={Building2}
          color="#3b82f6"
          href="/institutions"
        />
        <MetricCard
          label="Active Approvals"
          value={data.metrics.active_approvals}
          icon={CheckCircle2}
          color="#10b981"
          href="/institutions"
        />
        <MetricCard
          label="Student Records"
          value={data.metrics.student_records.toLocaleString()}
          icon={GraduationCap}
          color="#06b6d4"
          href="/students"
        />
        <MetricCard
          label="Pending Submissions"
          value={data.metrics.pending_submissions}
          icon={Upload}
          color="#8b5cf6"
          href="/upload"
        />
        <MetricCard
          label="Validation Issues"
          value={data.metrics.validation_issues}
          icon={AlertTriangle}
          color="#f97316"
          href="/validation"
        />
        <MetricCard
          label="Open Cases"
          value={data.metrics.open_cases}
          icon={FolderSearch}
          color="#ef4444"
          href="/cases"
        />
      </div>

      {/* Charts & Operational Intelligence */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Cases by Risk Band */}
        <Card className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-sm text-slate-200 flex items-center gap-2">
                <Activity size={16} className="text-cyan-400" />
                Investigation Cases by Risk Score Band
              </h3>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Deterministic rule scoring (0–100) based on intake violations and cross-institution duplicates.
              </p>
            </div>
            <Link
              href="/risk"
              className="text-xs text-cyan-400 hover:text-cyan-300 font-medium flex items-center gap-1"
            >
              View Cases <ArrowUpRight size={13} />
            </Link>
          </div>

          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={riskData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
              <XAxis
                dataKey="band"
                tick={{ fill: "#94a3b8", fontSize: 11 }}
                axisLine={{ stroke: "#1e293b" }}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: "#94a3b8", fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                contentStyle={{
                  background: "#0f172a",
                  border: "1px solid #334155",
                  borderRadius: 8,
                  fontSize: 12,
                  color: "#f1f5f9",
                }}
              />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {riskData.map((entry, idx) => (
                  <Cell key={idx} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* Priority Alerts */}
        <Card>
          <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-2.5">
            <h3 className="font-semibold text-sm text-slate-200 flex items-center gap-2">
              <AlertTriangle size={16} className="text-rose-400" />
              Priority Alerts ({data.alerts.length})
            </h3>
            <span className="text-[10px] font-mono text-slate-400">Real-time</span>
          </div>

          {data.alerts.length === 0 ? (
            <p className="text-xs text-center py-12 text-slate-500">
              No active critical alerts detected across institutions.
            </p>
          ) : (
            <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
              {data.alerts.slice(0, 8).map((alert, i) => (
                <div
                  key={i}
                  className="p-2.5 rounded-lg border border-slate-800/80 bg-slate-900/50 flex items-start gap-2.5"
                >
                  <span
                    className="w-2 h-2 rounded-full shrink-0 mt-1"
                    style={{
                      background: alert.severity === "critical" ? "#ef4444" : "#f97316",
                    }}
                  />
                  <span className="text-xs text-slate-300 leading-snug">{alert.message}</span>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* Intake Reconciliation & Audit Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Intake Reconciliation */}
        <Card>
          <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-2.5">
            <div>
              <h3 className="font-semibold text-sm text-slate-200 flex items-center gap-2">
                <CheckSquare size={16} className="text-cyan-400" />
                Intake Capacity Reconciliation
              </h3>
              <p className="text-[11px] text-slate-400">AICTE Approved Seats vs. Submitted Student Count</p>
            </div>
            <Link
              href="/validation"
              className="text-xs text-cyan-400 hover:text-cyan-300 font-medium flex items-center gap-1"
            >
              Reconcile All <ArrowUpRight size={13} />
            </Link>
          </div>

          {data.intake_reconciliation.length === 0 ? (
            <p className="text-xs text-center py-10 text-slate-500">
              No reconciliation records found in active academic year.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-left text-slate-400 border-b border-slate-800">
                    <th className="pb-2 font-semibold">Institution</th>
                    <th className="pb-2 font-semibold">Course</th>
                    <th className="pb-2 font-semibold text-right">Approved</th>
                    <th className="pb-2 font-semibold text-right">Actual</th>
                    <th className="pb-2 font-semibold text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {data.intake_reconciliation.slice(0, 6).map((r, i) => (
                    <tr key={i} className="table-row-hover">
                      <td className="py-2.5 font-medium text-slate-200 truncate max-w-[150px]">
                        {r.institution_name}
                      </td>
                      <td className="py-2.5 text-slate-300 truncate max-w-[120px]">{r.course_name}</td>
                      <td className="py-2.5 text-right font-mono text-slate-300">{r.approved_intake}</td>
                      <td className="py-2.5 text-right font-mono font-bold text-slate-100">{r.actual_enrolment}</td>
                      <td className="py-2.5 text-right">
                        <StatusBadge status={r.status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        {/* Recent Audit Timeline */}
        <Card>
          <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-2.5">
            <div>
              <h3 className="font-semibold text-sm text-slate-200 flex items-center gap-2">
                <FolderSearch size={16} className="text-indigo-400" />
                Immutable Audit Trail Activity
              </h3>
              <p className="text-[11px] text-slate-400">Chronological governance log across all roles</p>
            </div>
            <Link
              href="/audit"
              className="text-xs text-cyan-400 hover:text-cyan-300 font-medium flex items-center gap-1"
            >
              Full Log <ArrowUpRight size={13} />
            </Link>
          </div>

          {data.recent_audit_activity.length === 0 ? (
            <p className="text-xs text-center py-10 text-slate-500">No recent audit actions logged.</p>
          ) : (
            <div className="space-y-2.5 max-h-56 overflow-y-auto pr-1">
              {data.recent_audit_activity.map((a) => (
                <div
                  key={a.id}
                  className="flex items-center justify-between p-2 rounded-lg bg-slate-900/40 border border-slate-800/80 text-xs"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="font-semibold text-slate-200">{a.action}</span>
                    {a.actor_role && (
                      <span className="font-mono text-[10px] text-cyan-400 bg-cyan-500/10 px-1.5 py-0.5 rounded border border-cyan-500/20">
                        {a.actor_role}
                      </span>
                    )}
                  </div>
                  <span className="text-[11px] text-slate-400 font-mono">
                    {formatDate(a.created_at)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
