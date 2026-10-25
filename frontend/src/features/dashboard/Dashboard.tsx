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
} from "lucide-react";
import { Card, MetricCard, StatusBadge } from "@/components/ui/Card";
import { formatDate } from "@/lib/utils";
import {
  type DashboardData,
  RISK_BAND_COLORS,
  STATUS_COLORS,
} from "@/types";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

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
      <div className="flex items-center justify-center h-64">
        <div
          className="w-8 h-8 border-2 rounded-full animate-spin"
          style={{
            borderColor: "var(--accent)",
            borderTopColor: "transparent",
          }}
        />
      </div>
    );

  if (error)
    return (
      <Card>
        <p className="text-red-400 text-sm">Error: {error}</p>
      </Card>
    );

  if (!data) return null;

  const riskData = [
    { band: "Low", count: data.cases_by_risk.low, fill: "#22c55e" },
    { band: "Medium", count: data.cases_by_risk.medium, fill: "#eab308" },
    { band: "High", count: data.cases_by_risk.high, fill: "#f97316" },
    { band: "Critical", count: data.cases_by_risk.critical, fill: "#ef4444" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">AICTE Command Centre</h1>
        <div className="flex items-center gap-2 mt-1">
          <span
            className="text-xs px-2 py-1 rounded-full border"
            style={{
              background: "rgba(6, 182, 212, 0.1)",
              borderColor: "rgba(6, 182, 212, 0.3)",
              color: "#06b6d4",
            }}
          >
            {data.demo_label || "SYNTHETIC DEMONSTRATION DATA"}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <MetricCard
          label="Institutions"
          value={data.metrics.total_institutions}
          icon={Building2}
          color="#3b82f6"
        />
        <MetricCard
          label="Active Approvals"
          value={data.metrics.active_approvals}
          icon={CheckCircle2}
          color="#22c55e"
        />
        <MetricCard
          label="Student Records"
          value={data.metrics.student_records.toLocaleString()}
          icon={GraduationCap}
          color="#06b6d4"
        />
        <MetricCard
          label="Pending Submissions"
          value={data.metrics.pending_submissions}
          icon={Upload}
          color="#8b5cf6"
        />
        <MetricCard
          label="Validation Issues"
          value={data.metrics.validation_issues}
          icon={AlertTriangle}
          color="#f97316"
        />
        <MetricCard
          label="Open Cases"
          value={data.metrics.open_cases}
          icon={FolderSearch}
          color="#ef4444"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <h3 className="font-semibold mb-4 text-sm">
            Cases by Risk Band
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={riskData}>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="var(--border)"
                vertical={false}
              />
              <XAxis
                dataKey="band"
                tick={{ fill: "var(--muted)", fontSize: 12 }}
                axisLine={{ stroke: "var(--border)" }}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: "var(--muted)", fontSize: 12 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                contentStyle={{
                  background: "var(--surface)",
                  border: "1px solid var(--border)",
                  borderRadius: 8,
                  fontSize: 12,
                }}
              />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {riskData.map((entry, idx) => (
                  <Bar key={idx} dataKey="count" fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h3 className="font-semibold mb-4 text-sm">Recent Alerts</h3>
          {data.alerts.length === 0 ? (
            <p className="text-sm text-center py-8" style={{ color: "var(--muted)" }}>
              No active alerts
            </p>
          ) : (
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {data.alerts.slice(0, 10).map((alert, i) => (
                <div
                  key={i}
                  className="flex items-start gap-2 p-2 rounded-lg"
                  style={{ background: "var(--background)" }}
                >
                  <AlertTriangle
                    size={16}
                    className="mt-0.5 shrink-0"
                    style={{
                      color:
                        alert.severity === "critical" ? "#ef4444" : "#f97316",
                    }}
                  />
                  <span className="text-xs">{alert.message}</span>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <h3 className="font-semibold mb-4 text-sm">
            Intake Reconciliation
          </h3>
          {data.intake_reconciliation.length === 0 ? (
            <p className="text-sm text-center py-8" style={{ color: "var(--muted)" }}>
              No reconciliation data available
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left" style={{ color: "var(--muted)" }}>
                    <th className="pb-2 font-medium text-xs">Institution</th>
                    <th className="pb-2 font-medium text-xs">Course</th>
                    <th className="pb-2 font-medium text-xs text-right">Approved</th>
                    <th className="pb-2 font-medium text-xs text-right">Actual</th>
                    <th className="pb-2 font-medium text-xs text-right">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {data.intake_reconciliation.map((r, i) => (
                    <tr key={i} className="border-t" style={{ borderColor: "var(--border)" }}>
                      <td className="py-2 text-xs">{r.institution_name}</td>
                      <td className="py-2 text-xs">{r.course_name}</td>
                      <td className="py-2 text-xs text-right tabular-nums">{r.approved_intake}</td>
                      <td className="py-2 text-xs text-right tabular-nums">{r.actual_enrolment}</td>
                      <td className="py-2 text-right">
                        <span className={`badge text-xs ${r.status === "exceeds_intake" ? "text-red-600 bg-red-50 border border-red-200" : "text-green-600 bg-green-50 border border-green-200"}`}>
                          {r.status === "exceeds_intake" ? "Exceeds" : "Within"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        <Card>
          <h3 className="font-semibold mb-4 text-sm">Recent Audit Activity</h3>
          {data.recent_audit_activity.length === 0 ? (
            <p className="text-sm text-center py-8" style={{ color: "var(--muted)" }}>
              No recent activity
            </p>
          ) : (
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {data.recent_audit_activity.map((a) => (
                <div
                  key={a.id}
                  className="flex items-center justify-between p-2 rounded-lg"
                  style={{ background: "var(--background)" }}
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-xs font-medium">{a.action}</span>
                    {a.actor_role && (
                      <span className="text-xs" style={{ color: "var(--muted)" }}>
                        ({a.actor_role})
                      </span>
                    )}
                  </div>
                  <span className="text-xs" style={{ color: "var(--muted)" }}>
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
