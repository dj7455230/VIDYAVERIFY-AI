"use client";

import { useState } from "react";
import { AppShell } from "@/components/AppShell";
import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";
import { Upload, FileSpreadsheet, ArrowRight, CheckCircle2 } from "lucide-react";

export default function UploadPage() {
  return (
    <AppShell>
      <UploadView />
    </AppShell>
  );
}

function UploadView() {
  const [institutionId, setInstitutionId] = useState("");
  const [academicYearId, setAcademicYearId] = useState("");
  const [institutions, setInstitutions] = useState<any[]>([]);
  const [years, setYears] = useState<any[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");

  useState(() => {
    api.get("/institutions?page=1&page_size=100").then((d: any) => setInstitutions(d.items)).catch(() => {});
    api.get("/academic-years").then((d: any) => setYears(d.items)).catch(() => {});
  });

  const handleUpload = async () => {
    if (!file || !institutionId || !academicYearId) {
      setError("Please select institution, academic year, and file.");
      return;
    }
    setUploading(true);
    setError("");
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("institution_id", institutionId);
      fd.append("academic_year_id", academicYearId);
      const res = await api.postForm("/submissions/upload", fd);
      setResult(res);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setUploading(false);
    }
  };

  const handleValidate = async () => {
    if (!result?.batch_id) return;
    try {
      const res = await api.post(`/submissions/${result.batch_id}/validate`);
      setResult({ ...result, validation: res });
    } catch (e: any) {
      setError(e.message);
    }
  };

  return (
    <div className="space-y-4 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Upload size={24} /> Smart Upload Studio
        </h1>
        <p className="text-sm" style={{ color: "var(--muted)" }}>
          CSV/XLSX student record ingestion with validation
        </p>
      </div>

      <Card>
        <h3 className="font-semibold mb-4 text-sm">Step 1: Select Institution and Academic Year</h3>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium mb-1" style={{ color: "var(--muted)" }}>Institution</label>
            <select
              value={institutionId}
              onChange={(e) => setInstitutionId(e.target.value)}
              className="w-full px-3 py-2 rounded-lg text-sm"
              style={{ background: "var(--background)", border: "1px solid var(--border)", color: "var(--foreground)" }}
            >
              <option value="">Select institution...</option>
              {institutions.map((i) => (
                <option key={i.id} value={i.id}>{i.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium mb-1" style={{ color: "var(--muted)" }}>Academic Year</label>
            <select
              value={academicYearId}
              onChange={(e) => setAcademicYearId(e.target.value)}
              className="w-full px-3 py-2 rounded-lg text-sm"
              style={{ background: "var(--background)", border: "1px solid var(--border)", color: "var(--foreground)" }}
            >
              <option value="">Select year...</option>
              {years.map((y) => (
                <option key={y.id} value={y.id}>{y.year_code}</option>
              ))}
            </select>
          </div>
        </div>
      </Card>

      <Card>
        <h3 className="font-semibold mb-4 text-sm">Step 2: Upload File (CSV or XLSX, max 10MB)</h3>
        <div
          className="border-2 border-dashed rounded-lg p-8 text-center"
          style={{ borderColor: "var(--border)" }}
          onDrop={(e) => { e.preventDefault(); if (e.dataTransfer.files[0]) setFile(e.dataTransfer.files[0]); }}
          onDragOver={(e) => e.preventDefault()}
        >
          <FileSpreadsheet size={32} className="mx-auto mb-2" style={{ color: "var(--muted)" }} />
          <input
            type="file"
            accept=".csv,.xlsx"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="hidden"
            id="file-input"
          />
          <label htmlFor="file-input" className="cursor-pointer text-sm hover:text-cyan-400" style={{ color: "var(--muted)" }}>
            {file ? file.name : "Click to select or drag a file here"}
          </label>
        </div>
        <button
          onClick={handleUpload}
          disabled={!file || !institutionId || !academicYearId || uploading}
          className="w-full mt-3 py-2.5 rounded-lg font-medium text-sm text-white disabled:opacity-50"
          style={{ background: "var(--accent)" }}
        >
          {uploading ? "Uploading..." : "Upload File"}
        </button>
        {error && <p className="text-xs text-red-400 mt-2">{error}</p>}
      </Card>

      {result && (
        <Card>
          <h3 className="font-semibold mb-3 text-sm flex items-center gap-2">
            <CheckCircle2 size={16} className="text-green-500" />
            Upload Successful — {result.total_rows} rows detected
          </h3>
          <p className="text-xs" style={{ color: "var(--muted)" }}>Detected headers: {result.detected_headers.join(", ")}</p>
          <p className="text-xs mt-1" style={{ color: "var(--muted)" }}>Canonical columns: {result.canonical_columns.join(", ")}</p>
          <div className="mt-3 p-3 rounded-lg" style={{ background: "var(--background)" }}>
            <p className="text-xs font-medium mb-2">Preview (first 5 rows):</p>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-left" style={{ color: "var(--muted)" }}>
                    {result.detected_headers.slice(0, 6).map((h: string) => (
                      <th key={h} className="px-2 py-1 font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {result.preview.slice(0, 5).map((row: any, i: number) => (
                    <tr key={i} style={{ borderBottom: "1px solid var(--border)" }}>
                      {result.detected_headers.slice(0, 6).map((h: string) => (
                        <td key={h} className="px-2 py-1">{String(row[h] || "").slice(0, 30)}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <button
            onClick={handleValidate}
            className="w-full mt-3 py-2.5 rounded-lg font-medium text-sm text-white flex items-center justify-center gap-2"
            style={{ background: "var(--accent)" }}
          >
            Run Validation <ArrowRight size={14} />
          </button>
          {result.validation && (
            <div className="mt-3 p-3 rounded-lg" style={{ background: "var(--background)" }}>
              <p className="text-sm font-medium mb-2">
                Validation: {result.validation.status === "validated" ? (
                  <span className="text-green-500">No issues found</span>
                ) : (
                  <span className="text-orange-500">{result.validation.issues_count} issue(s) found</span>
                )}
              </p>
              <p className="text-xs" style={{ color: "var(--muted)" }}>
                Valid rows: {result.validation.valid_rows} / Invalid rows: {result.validation.invalid_rows}
              </p>
              {result.validation.issues_by_severity.critical > 0 && (
                <p className="text-xs text-red-400 mt-1">Critical: {result.validation.issues_by_severity.critical}</p>
              )}
              {result.validation.issues_by_severity.error > 0 && (
                <p className="text-xs text-orange-400 mt-1">Errors: {result.validation.issues_by_severity.error}</p>
              )}
              {result.validation.issues_by_severity.warning > 0 && (
                <p className="text-xs text-yellow-400 mt-1">Warnings: {result.validation.issues_by_severity.warning}</p>
              )}
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
