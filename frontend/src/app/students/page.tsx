"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";
import { type StudentRecord, type PaginatedResponse } from "@/types";
import { Search, ChevronLeft, ChevronRight } from "lucide-react";

export default function StudentsPage() {
  return (
    <AppShell>
      <StudentsView />
    </AppShell>
  );
}

function StudentsView() {
  const [data, setData] = useState<PaginatedResponse<StudentRecord> | null>(null);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams({
      page: String(page),
      page_size: "20",
    });
    if (search) params.set("search", search);
    api
      .get<PaginatedResponse<StudentRecord>>(`/students?${params}`)
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [search, page]);

  const verifColors: Record<string, string> = {
    verified: "text-green-600 bg-green-50 border-green-200",
    unverified: "text-gray-600 bg-gray-50 border-gray-200",
    pending: "text-yellow-600 bg-yellow-50 border-yellow-200",
    failed: "text-red-600 bg-red-50 border-red-200",
  };

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold">Student Records</h1>
        <p className="text-sm" style={{ color: "var(--muted)" }}>
          Authorized student record registry — identifiers masked
        </p>
      </div>

      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: "var(--muted)" }} />
          <input
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            placeholder="Search by name or APAAR reference..."
            className="w-full pl-9 pr-3 py-2 rounded-lg text-sm"
            style={{ background: "var(--surface)", border: "1px solid var(--border)", color: "var(--foreground)" }}
          />
        </div>
      </div>

      {loading ? (
        <div className="text-center py-8" style={{ color: "var(--muted)" }}>Loading...</div>
      ) : (
        <>
          <Card className="p-0 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left" style={{ color: "var(--muted)", borderBottom: "1px solid var(--border)" }}>
                    <th className="px-4 py-3 font-medium text-xs">APAAR (Masked)</th>
                    <th className="px-4 py-3 font-medium text-xs">Name</th>
                    <th className="px-4 py-3 font-medium text-xs">Institution</th>
                    <th className="px-4 py-3 font-medium text-xs">Course</th>
                    <th className="px-4 py-3 font-medium text-xs">Admission</th>
                    <th className="px-4 py-3 font-medium text-xs">Verification</th>
                  </tr>
                </thead>
                <tbody>
                  {data?.items.map((s) => (
                    <tr key={s.id} className="hover:bg-slate-700/30 transition-colors" style={{ borderBottom: "1px solid var(--border)" }}>
                      <td className="px-4 py-3 font-mono text-xs">{s.apaar_reference_masked}</td>
                      <td className="px-4 py-3">
                        <a href={`/students/${s.id}`} className="hover:text-cyan-400 font-medium">{s.student_name}</a>
                      </td>
                      <td className="px-4 py-3 text-xs">{s.institution_name}</td>
                      <td className="px-4 py-3 text-xs">{s.course_name}</td>
                      <td className="px-4 py-3">
                        <span className="badge text-xs text-blue-600 bg-blue-50 border border-blue-200 capitalize">{s.admission_status}</span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`badge text-xs border capitalize ${verifColors[s.verification_status] || ""}`}>
                          {s.verification_status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
          {data && data.total_pages > 1 && (
            <div className="flex items-center justify-between">
              <span className="text-xs" style={{ color: "var(--muted)" }}>
                Page {data.page} of {data.total_pages} ({data.total} total)
              </span>
              <div className="flex gap-1">
                <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="p-1.5 rounded disabled:opacity-30" style={{ background: "var(--surface)" }}>
                  <ChevronLeft size={16} />
                </button>
                <button onClick={() => setPage(p => p + 1)} disabled={page >= (data?.total_pages || 1)} className="p-1.5 rounded disabled:opacity-30" style={{ background: "var(--surface)" }}>
                  <ChevronRight size={16} />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
