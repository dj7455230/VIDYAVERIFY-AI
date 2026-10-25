"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";
import { formatDate, formatDateTime } from "@/lib/utils";
import { ArrowLeft, ShieldCheck } from "lucide-react";

export default function StudentDetailPage() {
  return (
    <AppShell>
      <StudentDetail />
    </AppShell>
  );
}

function StudentDetail() {
  const params = useParams();
  const id = params.id as string;
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [verifMsg, setVerifMsg] = useState("");

  useEffect(() => {
    api.get(`/students/${id}`).then(setData).catch(() => {}).finally(() => setLoading(false));
  }, [id]);

  const requestVerification = async () => {
    try {
      const res: any = await api.post("/verification/request", { student_id: id });
      setVerifMsg(`Verification completed: ${res.status} (simulated)`);
      api.get(`/students/${id}`).then(setData);
    } catch (e: any) { setVerifMsg(e.message); }
  };

  if (loading) return <div className="text-center py-8" style={{ color: "var(--muted)" }}>Loading...</div>;
  if (!data) return <Card><p>Student record not found</p></Card>;

  const verifColors: Record<string, string> = {
    verified: "text-green-600 bg-green-50 border-green-200",
    unverified: "text-gray-600 bg-gray-50 border-gray-200",
    pending: "text-yellow-600 bg-yellow-50 border-yellow-200",
    failed: "text-red-600 bg-red-50 border-red-200",
  };

  return (
    <div className="space-y-4">
      <a href="/students" className="flex items-center gap-1 text-sm hover:text-cyan-400" style={{ color: "var(--muted)" }}>
        <ArrowLeft size={14} /> Back to Students
      </a>
      <div>
        <p className="font-mono text-xs" style={{ color: "var(--muted)" }}>{data.apaar_reference_masked}</p>
        <h1 className="text-2xl font-bold">{data.student_name}</h1>
        <p className="text-sm" style={{ color: "var(--muted)" }}>{data.institution_name} · {data.course_name}</p>
        <p className="text-xs mt-1" style={{ color: "var(--muted)" }}>{data.demo_label}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card>
          <h3 className="text-sm font-semibold mb-3">Record Details</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between"><span style={{ color: "var(--muted)" }}>Academic Year:</span><span className="text-xs">{data.academic_year || "—"}</span></div>
            <div className="flex justify-between"><span style={{ color: "var(--muted)" }}>Admission Status:</span><span className={`badge text-xs capitalize ${data.admission_status === "enrolled" ? "text-green-600 bg-green-50 border border-green-200" : "text-blue-600 bg-blue-50 border border-blue-200"}`}>{data.admission_status}</span></div>
            <div className="flex justify-between"><span style={{ color: "var(--muted)" }}>Enrolment Status:</span><span className="text-xs capitalize">{data.enrolment_status}</span></div>
            <div className="flex justify-between"><span style={{ color: "var(--muted)" }}>Verification:</span><span className={`badge text-xs border capitalize ${verifColors[data.verification_status] || ""}`}>{data.verification_status}</span></div>
            <div className="flex justify-between"><span style={{ color: "var(--muted)" }}>Date of Birth:</span><span className="text-xs">{formatDate(data.date_of_birth)}</span></div>
            <div className="flex justify-between"><span style={{ color: "var(--muted)" }}>Gender:</span><span className="text-xs">{data.gender || "—"}</span></div>
            <div className="flex justify-between"><span style={{ color: "var(--muted)" }}>Source Row:</span><span className="text-xs">{data.source_row_number || "—"}</span></div>
            <div className="flex justify-between"><span style={{ color: "var(--muted)" }}>Created:</span><span className="text-xs">{formatDateTime(data.created_at)}</span></div>
          </div>
        </Card>

        <Card>
          <h3 className="text-sm font-semibold mb-3">Verification</h3>
          <p className="text-xs mb-3" style={{ color: "var(--muted)" }}>
            Request identity verification through the DEMO_SIMULATOR provider (simulated, not real).
          </p>
          <button
            onClick={requestVerification}
            className="w-full py-2 rounded-lg text-sm text-white flex items-center justify-center gap-2"
            style={{ background: "var(--accent)" }}
          >
            <ShieldCheck size={16} /> Request Verification
          </button>
          {verifMsg && <p className="text-xs mt-2 text-center" style={{ color: verifMsg.includes("Error") ? "#ef4444" : "#22c55e" }}>{verifMsg}</p>}
          <div className="mt-3 p-2 rounded-lg text-xs text-center" style={{ background: "rgba(234, 179, 8, 0.08)", color: "#eab308" }}>
            Simulated verification only — NOT real APAAR verification
          </div>
        </Card>

        <Card>
          <h3 className="text-sm font-semibold mb-3">Enrolments</h3>
          {data.enrolments.length === 0 ? (
            <p className="text-sm" style={{ color: "var(--muted)" }}>No enrolment records.</p>
          ) : (
            <div className="space-y-2">
              {data.enrolments.map((e: any) => (
                <div key={e.id} className="p-2 rounded-lg" style={{ background: "var(--background)" }}>
                  <p className="text-xs font-mono">{e.enrolment_number}</p>
                  <p className="text-xs" style={{ color: "var(--muted)" }}>Status: {e.status}</p>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      <Card>
        <h3 className="text-sm font-semibold mb-3">Related Validation Issues</h3>
        {data.related_issues.length === 0 ? (
          <p className="text-sm" style={{ color: "var(--muted)" }}>No validation issues for this record.</p>
        ) : (
          <div className="space-y-2">
            {data.related_issues.map((i: any) => (
              <div key={i.id} className="p-2 rounded-lg" style={{ background: "var(--background)" }}>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono">{i.issue_code}</span>
                  <span className={`badge text-xs ${i.severity === "critical" ? "text-red-600 bg-red-50 border border-red-200" : i.severity === "error" ? "text-orange-600 bg-orange-50 border border-orange-200" : "text-yellow-600 bg-yellow-50 border border-yellow-200"}`}>{i.severity}</span>
                </div>
                <p className="text-xs mt-1">{i.explanation}</p>
                <p className="text-xs" style={{ color: "var(--muted)" }}>Status: {i.status}</p>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
