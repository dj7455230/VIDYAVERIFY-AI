"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { ArrowLeft } from "lucide-react";

export default function InstitutionDetailPage() {
  return (
    <AppShell>
      <InstitutionDetail />
    </AppShell>
  );
}

function InstitutionDetail() {
  const params = useParams();
  const id = params.id as string;
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get(`/institutions/${id}`).then(setData).catch(() => {}).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="text-center py-8" style={{ color: "var(--muted)" }}>Loading...</div>;
  if (!data) return <Card><p>Institution not found</p></Card>;

  return (
    <div className="space-y-4">
      <a href="/institutions" className="flex items-center gap-1 text-sm hover:text-cyan-400" style={{ color: "var(--muted)" }}>
        <ArrowLeft size={14} /> Back to Institutions
      </a>
      <div>
        <p className="font-mono text-xs" style={{ color: "var(--muted)" }}>{data.code}</p>
        <h1 className="text-2xl font-bold">{data.name}</h1>
        <p className="text-sm capitalize" style={{ color: "var(--muted)" }}>{data.institution_type} · {data.location}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <h3 className="text-sm font-semibold mb-3">Approvals</h3>
          {data.approvals.length === 0 ? (
            <p className="text-sm" style={{ color: "var(--muted)" }}>No approvals.</p>
          ) : (
            <div className="space-y-2">
              {data.approvals.map((a: any) => (
                <div key={a.id} className="flex items-center justify-between p-2 rounded-lg" style={{ background: "var(--background)" }}>
                  <span className="text-xs">Academic Year: {a.academic_year_id.slice(0, 8)}...</span>
                  <span className={`badge text-xs border ${a.approval_status === "approved" ? "text-green-600 bg-green-50 border-green-200" : "text-yellow-600 bg-yellow-50 border-yellow-200"} capitalize`}>
                    {a.approval_status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card>
          <h3 className="text-sm font-semibold mb-3">Intake Reconciliation</h3>
          {data.intake_approvals.length === 0 ? (
            <p className="text-sm" style={{ color: "var(--muted)" }}>No intake data.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-left" style={{ color: "var(--muted)" }}>
                    <th className="pb-2 font-medium">Course</th>
                    <th className="pb-2 font-medium text-right">Approved</th>
                    <th className="pb-2 font-medium text-right">Actual</th>
                    <th className="pb-2 font-medium text-right">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {data.intake_approvals.map((i: any) => (
                    <tr key={i.id} style={{ borderBottom: "1px solid var(--border)" }}>
                      <td className="py-2">{i.course_name}</td>
                      <td className="py-2 text-right tabular-nums">{i.approved_intake}</td>
                      <td className="py-2 text-right tabular-nums">{i.actual_enrolment}</td>
                      <td className="py-2 text-right">
                        <span className={`badge text-xs ${i.status === "exceeds_intake" ? "text-red-600 bg-red-50 border border-red-200" : "text-green-600 bg-green-50 border border-green-200"}`}>
                          {i.status === "exceeds_intake" ? "Exceeds" : "Within"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>

      <Card>
        <h3 className="text-sm font-semibold mb-3">Recent Submissions</h3>
        {data.recent_submissions.length === 0 ? (
          <p className="text-sm" style={{ color: "var(--muted)" }}>No submissions.</p>
        ) : (
          <div className="space-y-2">
            {data.recent_submissions.map((s: any) => (
              <div key={s.id} className="flex items-center justify-between p-2 rounded-lg" style={{ background: "var(--background)" }}>
                <span className="text-xs">Version {s.version} · {s.total_rows} rows</span>
                <span className={`badge text-xs ${s.status === "validated" ? "text-green-600 bg-green-50 border border-green-200" : s.status === "issues_found" ? "text-orange-600 bg-orange-50 border border-orange-200" : "text-blue-600 bg-blue-50 border border-blue-200"}`}>
                  {s.status.replace(/_/g, " ")}
                </span>
              </div>
            ))}
          </div>
        )}
      </Card>

      <Card>
        <h3 className="text-sm font-semibold mb-3">Open Clarification Requests</h3>
        {data.open_clarifications.length === 0 ? (
          <p className="text-sm" style={{ color: "var(--muted)" }}>No open clarification requests.</p>
        ) : (
          <div className="space-y-2">
            {data.open_clarifications.map((c: any) => (
              <div key={c.id} className="p-2 rounded-lg" style={{ background: "var(--background)" }}>
                <p className="text-xs font-medium">{c.subject}</p>
                <p className="text-xs" style={{ color: "var(--muted)" }}>{c.request_reference}</p>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
