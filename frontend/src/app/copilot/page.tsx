"use client";

import { useEffect, useRef, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";
import { Bot, Send, Sparkles } from "lucide-react";
import type { CopilotResponse } from "@/types";

export default function CopilotPage() {
  return (
    <AppShell>
      <CopilotView />
    </AppShell>
  );
}

function CopilotView() {
  const [messages, setMessages] = useState<{ q: string; a: CopilotResponse }[]>([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  const suggestions = [
    "Which institutions have the most unresolved validation issues?",
    "Summarize unresolved discrepancies for the current academic year.",
    "Which cases are awaiting an institution response?",
    "Show the intake reconciliation.",
  ];

  useEffect(() => {
    scrollRef.current?.scrollTo(0, scrollRef.current.scrollHeight);
  }, [messages]);

  const ask = async (q: string) => {
    if (!q.trim()) return;
    setLoading(true);
    setError("");
    try {
      const res = await api.post<CopilotResponse>("/copilot/query", { question: q });
      setMessages((prev) => [...prev, { q, a: res }]);
      setQuestion("");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Bot size={24} /> AI Compliance Copilot
        </h1>
        <p className="text-sm" style={{ color: "var(--muted)" }}>
          Grounded in authorized data. Deterministic fallback when no LLM is configured.
        </p>
      </div>

      <div
        className="p-3 rounded-lg text-xs border text-center"
        style={{ background: "rgba(6, 182, 212, 0.08)", borderColor: "rgba(6, 182, 212, 0.3)", color: "#06b6d4" }}
      >
        SYNTHETIC DEMONSTRATION DATA — Copilot uses authorized scope only. No arbitrary SQL execution.
      </div>

      <Card className="p-0">
        <div ref={scrollRef} className="h-96 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="text-center py-12">
              <Sparkles size={32} className="mx-auto mb-3" style={{ color: "var(--accent)" }} />
              <p className="text-sm" style={{ color: "var(--muted)" }}>
                Ask a question about your authorized data.
              </p>
              <div className="flex flex-wrap gap-2 justify-center mt-4 max-w-md mx-auto">
                {suggestions.map((s) => (
                  <button
                    key={s}
                    onClick={() => ask(s)}
                    className="px-3 py-1.5 rounded-lg text-xs border hover:border-cyan-500/50 transition-colors"
                    style={{ background: "var(--background)", borderColor: "var(--border)", color: "var(--muted)" }}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg, i) => (
              <div key={i} className="space-y-2">
                <div className="flex justify-end">
                  <div className="max-w-[80%] px-3 py-2 rounded-lg text-sm" style={{ background: "var(--accent)", color: "white" }}>
                    {msg.q}
                  </div>
                </div>
                <div className="flex justify-start">
                  <div className="max-w-[80%] px-3 py-2 rounded-lg text-sm" style={{ background: "var(--background)", border: "1px solid var(--border)" }}>
                    <div className="whitespace-pre-wrap">{msg.a.answer}</div>
                    <div className="mt-2 pt-2 border-t flex items-center gap-2 text-xs" style={{ borderColor: "var(--border)", color: "var(--muted)" }}>
                      <span className={`badge text-xs ${msg.a.is_llm ? "text-green-600 bg-green-50 border border-green-200" : "text-blue-600 bg-blue-50 border border-blue-200"}`}>
                        {msg.a.is_llm ? "LLM" : "Deterministic"}
                      </span>
                      <span>Provider: {msg.a.provider}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
          {loading && (
            <div className="flex justify-start">
              <div className="px-3 py-2 rounded-lg text-sm" style={{ background: "var(--background)", border: "1px solid var(--border)" }}>
                <span className="animate-pulse">Thinking...</span>
              </div>
            </div>
          )}
        </div>

        <div className="border-t p-3" style={{ borderColor: "var(--border)" }}>
          {error && <p className="text-xs text-red-400 mb-2">{error}</p>}
          <div className="flex gap-2">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter" && !loading) ask(question); }}
              placeholder="Ask about issues, risk scores, intake, duplicates..."
              className="flex-1 px-3 py-2 rounded-lg text-sm"
              style={{ background: "var(--background)", border: "1px solid var(--border)", color: "var(--foreground)" }}
              disabled={loading}
            />
            <button
              onClick={() => ask(question)}
              disabled={loading || !question.trim()}
              className="px-4 py-2 rounded-lg text-sm font-medium text-white disabled:opacity-50"
              style={{ background: "var(--accent)" }}
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      </Card>
    </div>
  );
}
