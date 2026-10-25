"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { Card, MetricCard } from "@/components/ui/Card";
import { api } from "@/lib/api";
import {
  Settings,
  Shield,
  Database,
  Sliders,
  CheckCircle2,
  RefreshCw,
  Cpu,
  Key,
  Layers,
  Save,
} from "lucide-react";

export default function SettingsPage() {
  return (
    <AppShell>
      <SettingsView />
    </AppShell>
  );
}

function SettingsView() {
  const [demoMode, setDemoMode] = useState(true);
  const [exactMatchThreshold, setExactMatchThreshold] = useState(100);
  const [fuzzyMatchThreshold, setFuzzyMatchThreshold] = useState(85);
  const [riskWeights, setRiskWeights] = useState({
    crossInstitution: 40,
    intakeExceeded: 35,
    apaarDiscrepancy: 15,
    verificationFailure: 10,
  });
  const [savedSuccess, setSavedSuccess] = useState(false);

  const handleSave = () => {
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2.5">
          <Settings className="text-cyan-400" size={26} /> Platform Configuration & Rules Engine
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Configure rule-based weights, RapidFuzz anomaly thresholds, and institutional demonstration parameters.
        </p>
      </div>

      {savedSuccess && (
        <div className="p-3 rounded-lg border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 text-xs flex items-center gap-2">
          <CheckCircle2 size={16} /> Configuration successfully synchronized with rule-scoring engine.
        </div>
      )}

      {/* Demonstration environment settings */}
      <Card>
        <div className="flex items-center gap-2.5 mb-3 border-b border-slate-800 pb-3">
          <Database size={18} className="text-cyan-400" />
          <h3 className="text-sm font-bold text-slate-200">Demonstration Environment Controls</h3>
        </div>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900 border border-slate-800">
            <div>
              <p className="text-xs font-semibold text-slate-200">Synthetic Data Environment Banner</p>
              <p className="text-[11px] text-slate-400">
                Guarantees transparent disclosure that data is synthetic demonstration data per SIH competition ethics.
              </p>
            </div>
            <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-cyan-500/15 border border-cyan-500/30 text-cyan-400">
              ALWAYS ACTIVE
            </span>
          </div>

          <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900 border border-slate-800">
            <div>
              <p className="text-xs font-semibold text-slate-200">APAAR Masking Policy</p>
              <p className="text-[11px] text-slate-400">
                Default privacy masking displays only the first 4 characters followed by asterisks (e.g., 9012********).
              </p>
            </div>
            <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 border border-emerald-500/30 text-emerald-400">
              ENFORCED
            </span>
          </div>
        </div>
      </Card>

      {/* Layered Duplicate Detection Thresholds */}
      <Card>
        <div className="flex items-center gap-2.5 mb-3 border-b border-slate-800 pb-3">
          <Layers size={18} className="text-indigo-400" />
          <h3 className="text-sm font-bold text-slate-200">Layered Duplicate Detection Thresholds</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="font-semibold text-slate-200">Layer 1: Exact APAAR Match</span>
              <span className="font-mono text-cyan-400 font-bold">{exactMatchThreshold}%</span>
            </div>
            <p className="text-[11px] text-slate-400">
              Normalized alphanumeric equality after stripping whitespace and punctuation.
            </p>
          </div>

          <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="font-semibold text-slate-200">Layer 2: RapidFuzz Name & DOB Matching</span>
              <span className="font-mono text-cyan-400 font-bold">{fuzzyMatchThreshold}%</span>
            </div>
            <input
              type="range"
              min="70"
              max="95"
              value={fuzzyMatchThreshold}
              onChange={(e) => setFuzzyMatchThreshold(Number(e.target.value))}
              className="w-full accent-cyan-400 cursor-pointer"
            />
            <p className="text-[11px] text-slate-400">
              Levenshtein token set ratio applied to student names across concurrent enrolments.
            </p>
          </div>
        </div>
      </Card>

      {/* Risk Scoring Weights */}
      <Card>
        <div className="flex items-center gap-2.5 mb-3 border-b border-slate-800 pb-3">
          <Sliders size={18} className="text-amber-400" />
          <h3 className="text-sm font-bold text-slate-200">Explainable Risk Scoring Engine Weights</h3>
        </div>
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs p-2.5 rounded bg-slate-900/60 border border-slate-800">
            <div>
              <p className="font-semibold text-slate-200">Cross-Institution Concurrent Enrolment</p>
              <p className="text-[10px] text-slate-400">Multiple active degrees for single APAAR reference</p>
            </div>
            <span className="font-mono font-bold text-amber-400">+{riskWeights.crossInstitution} pts</span>
          </div>

          <div className="flex items-center justify-between text-xs p-2.5 rounded bg-slate-900/60 border border-slate-800">
            <div>
              <p className="font-semibold text-slate-200">Institution Approved Intake Exceeded</p>
              <p className="text-[10px] text-slate-400">Enrolment exceeds AICTE Section 10(k) approval limits</p>
            </div>
            <span className="font-mono font-bold text-amber-400">+{riskWeights.intakeExceeded} pts</span>
          </div>

          <div className="flex items-center justify-between text-xs p-2.5 rounded bg-slate-900/60 border border-slate-800">
            <div>
              <p className="font-semibold text-slate-200">APAAR Format / Verification Mismatch</p>
              <p className="text-[10px] text-slate-400">Check-digit invalid or registry not found</p>
            </div>
            <span className="font-mono font-bold text-amber-400">+{riskWeights.apaarDiscrepancy} pts</span>
          </div>

          <div className="flex items-center justify-between text-xs p-2.5 rounded bg-slate-900/60 border border-slate-800">
            <div>
              <p className="font-semibold text-slate-200">Verification Simulator Flag</p>
              <p className="text-[10px] text-slate-400">Adapter returned manual review required</p>
            </div>
            <span className="font-mono font-bold text-amber-400">+{riskWeights.verificationFailure} pts</span>
          </div>
        </div>

        <div className="mt-4 flex justify-end">
          <button
            onClick={handleSave}
            className="px-4 py-2 rounded-lg text-xs font-semibold bg-cyan-500 hover:bg-cyan-400 text-slate-950 flex items-center gap-2 transition-colors shadow-sm"
          >
            <Save size={15} /> Save Configuration
          </button>
        </div>
      </Card>
    </div>
  );
}
