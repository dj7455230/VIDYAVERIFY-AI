"use client";

import { useState, useEffect } from "react";
import { AppShell } from "@/components/AppShell";
import { Card, MetricCard, StatusBadge } from "@/components/ui/Card";
import { api } from "@/lib/api";
import {
  Upload,
  FileSpreadsheet,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  Download,
  Info,
  Layers,
  Sparkles,
  FileText,
  RefreshCw,
} from "lucide-react";
import Link from "next/link";

export default function UploadPage() {
  return (
    <AppShell>
      <UploadStudioView />
    </AppShell>
  );
}

function UploadStudioView() {
  const [institutionId, setInstitutionId] = useState("");
  const [academicYearId, setAcademicYearId] = useState("");
  const [institutions, setInstitutions] = useState<any[]>([]);
  const [years, setYears] = useState<any[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [validating, setValidating] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");
  const [sampleLoaded, setSampleLoaded] = useState<string>("");

  useEffect(() => {
    api.get<any>("/institutions?page=1&page_size=100")
      .then((d) => {
        setInstitutions(d.items || []);
        if (d.items?.length) setInstitutionId(d.items[0].id);
      })
      .catch(() => {});
    api.get<any>("/academic-years")
      .then((d) => {
        setYears(d.items || []);
        if (d.items?.length) setAcademicYearId(d.items[0].id);
      })
      .catch(() => {});
  }, []);

  const handleDownloadSample = (type: "clean" | "issues") => {
    let csvContent = "";
    if (type === "clean") {
      csvContent = `apaar_reference,student_name,date_of_birth,gender,institution_code,course_code,academic_year,admission_status
901234567891,Aryan Sharma,2003-05-14,M,IITB001,CS101,2024-25,admitted
901234567892,Ananya Verma,2004-02-19,F,IITB001,CS101,2024-25,admitted
901234567893,Rohan Kulkarni,2003-11-08,M,IITB001,EC102,2024-25,admitted
901234567894,Sneha Patel,2004-08-22,F,IITB001,ME103,2024-25,admitted
901234567895,Vikram Singh,2003-01-30,M,IITB001,EE104,2024-25,admitted`;
    } else {
      csvContent = `apaar_reference,student_name,date_of_birth,gender,institution_code,course_code,academic_year,admission_status
901234567891,Aryan Sharma,2003-05-14,M,IITB001,CS101,2024-25,admitted
901234567891,Aryan Sharma Duplicate,2003-05-14,M,IITB001,CS101,2024-25,admitted
,Pooja Nair,2004-12-05,F,IITB001,CS101,2024-25,admitted
901234567897,Karan Mehra,INVALID_DATE,M,IITB001,CS101,2024-25,admitted
901234567898,Neha Gupta,2003-09-17,F,IITB001,INVALID_COURSE_999,2024-25,admitted`;
    }

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `vidyaverify_${type}_sample.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    // Also load as file in state for instant testing
    const sampleFile = new File([blob], `vidyaverify_${type}_sample.csv`, { type: "text/csv" });
    setFile(sampleFile);
    setSampleLoaded(type === "clean" ? "Clean Template" : "Imperfect Template (With Issues)");
  };

  const handleUpload = async () => {
    if (!file || !institutionId || !academicYearId) {
      setError("Please select an institution, academic year, and CSV/XLSX file.");
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
      setError(e.message || "Failed to upload file");
    } finally {
      setUploading(false);
    }
  };

  const handleValidate = async () => {
    if (!result?.batch_id) return;
    setValidating(true);
    try {
      const res = await api.post(`/submissions/${result.batch_id}/validate`);
      setResult({ ...result, validation: res });
    } catch (e: any) {
      setError(e.message || "Validation failed");
    } finally {
      setValidating(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2.5">
          <Upload className="text-cyan-400" size={26} /> Smart Upload Studio
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          High-throughput canonical CSV/XLSX student data ingestion with real-time schema mapping and rule validation.
        </p>
      </div>

      {/* Synthetic Templates Bar */}
      <Card className="bg-gradient-to-r from-slate-900 via-slate-900 to-cyan-950/20 border-cyan-500/20">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h4 className="text-xs font-bold text-cyan-400 uppercase tracking-wider flex items-center gap-1.5">
              <Sparkles size={14} /> SIH Demonstration Templates
            </h4>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Pre-built synthetic datasets designed to demonstrate clean ingestion or highlight deterministic rule errors.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => handleDownloadSample("clean")}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20 transition-colors flex items-center gap-1.5"
            >
              <Download size={13} /> Clean Sample
            </button>
            <button
              onClick={() => handleDownloadSample("issues")}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-amber-500/10 border border-amber-500/30 text-amber-400 hover:bg-amber-500/20 transition-colors flex items-center gap-1.5"
            >
              <AlertTriangle size={13} /> Imperfect Sample (Issues)
            </button>
          </div>
        </div>
        {sampleLoaded && (
          <p className="text-[11px] text-cyan-400 mt-2 font-mono">
            ✓ Loaded {sampleLoaded} into upload slot. Ready to ingest.
          </p>
        )}
      </Card>

      {/* Step 1: Select Institution & Academic Year */}
      <Card>
        <h3 className="font-semibold text-xs text-slate-300 uppercase tracking-wider mb-3">
          Step 1: Institutional Context & Target Cohort
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium mb-1 text-slate-400">Target AICTE Institution</label>
            <select
              value={institutionId}
              onChange={(e) => setInstitutionId(e.target.value)}
              className="w-full px-3 py-2 rounded-lg text-xs bg-slate-900 border border-slate-700 text-slate-200 focus:outline-none focus:border-cyan-500"
            >
              <option value="">Select institution...</option>
              {institutions.map((i) => (
                <option key={i.id} value={i.id}>
                  {i.code} — {i.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium mb-1 text-slate-400">Academic Year</label>
            <select
              value={academicYearId}
              onChange={(e) => setAcademicYearId(e.target.value)}
              className="w-full px-3 py-2 rounded-lg text-xs bg-slate-900 border border-slate-700 text-slate-200 focus:outline-none focus:border-cyan-500"
            >
              <option value="">Select academic year...</option>
              {years.map((y) => (
                <option key={y.id} value={y.id}>
                  {y.year_code} ({y.is_active ? "Current Active" : "Historical"})
                </option>
              ))}
            </select>
          </div>
        </div>
      </Card>

      {/* Step 2: Upload File */}
      <Card>
        <h3 className="font-semibold text-xs text-slate-300 uppercase tracking-wider mb-3">
          Step 2: CSV / XLSX File Ingestion (Max 10 MB)
        </h3>
        <div
          className="border-2 border-dashed rounded-xl p-8 text-center transition-colors hover:border-cyan-500/50"
          style={{ borderColor: "var(--border)" }}
          onDrop={(e) => {
            e.preventDefault();
            if (e.dataTransfer.files[0]) {
              setFile(e.dataTransfer.files[0]);
              setSampleLoaded("");
            }
          }}
          onDragOver={(e) => e.preventDefault()}
        >
          <FileSpreadsheet size={36} className="mx-auto mb-2 text-cyan-400" />
          <input
            type="file"
            accept=".csv,.xlsx"
            onChange={(e) => {
              setFile(e.target.files?.[0] || null);
              setSampleLoaded("");
            }}
            className="hidden"
            id="file-input"
          />
          <label
            htmlFor="file-input"
            className="cursor-pointer text-xs font-medium text-slate-300 hover:text-cyan-400 transition-colors block"
          >
            {file ? (
              <span className="font-semibold text-cyan-400 font-mono text-sm">
                Selected: {file.name} ({(file.size / 1024).toFixed(1)} KB)
              </span>
            ) : (
              <span>Click to select file or drag and drop CSV / Excel spreadsheet here</span>
            )}
          </label>
          <p className="text-[11px] text-slate-500 mt-1">
            Expected columns: apaar_reference, student_name, date_of_birth, course_code, academic_year, admission_status
          </p>
        </div>

        <button
          onClick={handleUpload}
          disabled={!file || !institutionId || !academicYearId || uploading}
          className="w-full mt-4 py-2.5 rounded-lg font-semibold text-xs text-slate-950 bg-cyan-500 hover:bg-cyan-400 disabled:opacity-40 transition-colors shadow-sm flex items-center justify-center gap-2"
        >
          {uploading ? (
            <>
              <RefreshCw size={14} className="animate-spin" /> Ingesting & Analyzing Schema...
            </>
          ) : (
            <>
              <Upload size={14} /> Ingest File & Preview Canonical Mapping
            </>
          )}
        </button>

        {error && (
          <p className="text-xs text-rose-400 mt-2 p-2 rounded bg-rose-500/10 border border-rose-500/20">
            {error}
          </p>
        )}
      </Card>

      {/* Step 3: Schema Mapping & Validation Preview */}
      {result && (
        <Card className="border-cyan-500/40 shadow-lg shadow-cyan-950/20">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-3">
            <h3 className="font-bold text-sm text-slate-100 flex items-center gap-2">
              <CheckCircle2 size={18} className="text-emerald-400" />
              Batch Created: #{result.batch_id.slice(0, 8)} ({result.total_rows} Total Records)
            </h3>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
              SHA256 Verified
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4 text-xs">
            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
              <p className="font-semibold text-slate-300 mb-1">Detected File Headers:</p>
              <p className="font-mono text-cyan-400 text-[11px] truncate">{result.detected_headers.join(", ")}</p>
            </div>
            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
              <p className="font-semibold text-slate-300 mb-1">Canonical Schema Target:</p>
              <p className="font-mono text-slate-400 text-[11px] truncate">{result.canonical_columns.join(", ")}</p>
            </div>
          </div>

          {/* First 5 rows preview */}
          <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 mb-4">
            <p className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
              Ingested Records Preview (First 5 Rows):
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-left text-slate-400 border-b border-slate-800">
                    {result.detected_headers.slice(0, 6).map((h: string) => (
                      <th key={h} className="px-2 py-1.5 font-semibold font-mono text-[11px]">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {result.preview.slice(0, 5).map((row: any, i: number) => (
                    <tr key={i} className="table-row-hover font-mono text-[11px]">
                      {result.detected_headers.slice(0, 6).map((h: string) => (
                        <td key={h} className="px-2 py-1.5 text-slate-300">
                          {String(row[h] || "").slice(0, 25)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Trigger Validation */}
          <button
            onClick={handleValidate}
            disabled={validating}
            className="w-full py-2.5 rounded-lg font-semibold text-xs text-slate-950 bg-cyan-500 hover:bg-cyan-400 transition-colors flex items-center justify-center gap-2 shadow-sm"
          >
            {validating ? (
              <>
                <RefreshCw size={14} className="animate-spin" /> Executing Deterministic Rule Engine...
              </>
            ) : (
              <>
                Execute Rule Validation & Check Intake Limits <ArrowRight size={14} />
              </>
            )}
          </button>

          {/* Validation Report */}
          {result.validation && (
            <div className="mt-4 p-4 rounded-xl bg-slate-900 border border-slate-700 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-200">
                  Validation Results:
                </span>
                <Link
                  href="/validation"
                  className="text-xs text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1"
                >
                  Inspect in Validation Engine <ArrowRight size={13} />
                </Link>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-center">
                  <p className="text-[10px] text-slate-400">Total Valid Rows</p>
                  <p className="text-xl font-bold font-mono text-emerald-400">
                    {result.validation.valid_rows}
                  </p>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-center">
                  <p className="text-[10px] text-slate-400">Invalid Rows</p>
                  <p className="text-xl font-bold font-mono text-rose-400">
                    {result.validation.invalid_rows}
                  </p>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-center">
                  <p className="text-[10px] text-slate-400">Total Issues Flagged</p>
                  <p className="text-xl font-bold font-mono text-amber-400">
                    {result.validation.issues_count}
                  </p>
                </div>
              </div>

              {result.validation.issues_count > 0 && (
                <div className="text-xs space-y-1 text-slate-300 pt-2 border-t border-slate-800">
                  {result.validation.issues_by_severity.critical > 0 && (
                    <p className="text-rose-400 font-semibold">
                      • {result.validation.issues_by_severity.critical} Critical Violations (e.g., Intake capacity exceeded)
                    </p>
                  )}
                  {result.validation.issues_by_severity.error > 0 && (
                    <p className="text-amber-400 font-semibold">
                      • {result.validation.issues_by_severity.error} Format / Missing Field Errors (e.g., Missing APAAR reference)
                    </p>
                  )}
                  {result.validation.issues_by_severity.warning > 0 && (
                    <p className="text-yellow-400 font-semibold">
                      • {result.validation.issues_by_severity.warning} Format Warnings
                    </p>
                  )}
                </div>
              )}
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
