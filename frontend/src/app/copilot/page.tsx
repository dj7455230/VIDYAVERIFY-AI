"use client";

import { useEffect, useRef, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";
import {
  Bot,
  Send,
  Sparkles,
  HelpCircle,
  RefreshCw,
  ExternalLink,
  ShieldCheck,
  AlertCircle,
  Cpu,
  Layers,
} from "lucide-react";
import Link from "next/link";

interface CopilotResponse {
  question: string;
  answer: string;
  evidence_refs?: any[];
  suggested_questions?: string[];
  provider: string;
  is_llm: boolean;
  mode: "llm" | "rule_based";
  is_synthetic: boolean;
  demo_label: string | null;
  request_id?: string;
}

interface Message {
  id: string;
  sender: "user" | "copilot";
  text: string;
  responseMeta?: CopilotResponse;
  timestamp: string;
}

export default function CopilotPage() {
  return (
    <AppShell>
      <CopilotView />
    </AppShell>
  );
}

function CopilotView() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retryQuery, setRetryQuery] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const predefinedPrompts = [
    "How many institutions are in the system?",
    "Which institutions have the most unresolved validation issues?",
    "Explain the risk score of this case.",
    "Which cases are waiting for clarification?",
    "Summarize intake discrepancies for an institution.",
    "What evidence supports this potential duplicate?",
    "Summarize validation issues for the current academic year.",
    "What changed after the latest record correction?",
  ];

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [messages, loading]);

  const handleSend = async (queryToSend?: string) => {
    const q = (queryToSend || question).trim();
    if (!q || loading) return;

    const userMessageId = `user-${Date.now()}`;
    const userMsg: Message = {
      id: userMessageId,
      sender: "user",
      text: q,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setQuestion("");
    setError(null);
    setRetryQuery(null);
    setLoading(true);

    try {
      const res = await api.post<CopilotResponse>("/copilot/query", { question: q });
      const copilotMsg: Message = {
        id: `copilot-${Date.now()}`,
        sender: "copilot",
        text: res.answer,
        responseMeta: res,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, copilotMsg]);
    } catch (err: any) {
      const errorMsg = err.message || "Failed to reach AI Compliance Copilot backend.";
      setError(errorMsg);
      setRetryQuery(q);
    } finally {
      setLoading(false);
      setTimeout(() => textareaRef.current?.focus(), 100);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="space-y-4 max-w-4xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2.5 text-slate-100">
            <Bot className="text-cyan-400" size={26} /> AI Compliance Copilot
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Grounded in institutional database records. Server-scoped by user role.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono px-2.5 py-1 rounded-full border border-cyan-500/30 bg-cyan-500/10 text-cyan-400 font-semibold flex items-center gap-1.5">
            <ShieldCheck size={13} /> SCOPED DATA ONLY
          </span>
        </div>
      </div>

      {/* Main Chat Container */}
      <Card className="p-0 overflow-hidden border-slate-800 bg-slate-900/60 shadow-xl flex flex-col h-[600px]">
        {/* Messages list */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center p-6 space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
                <Sparkles size={24} />
              </div>
              <div>
                <h3 className="font-semibold text-sm text-slate-200">
                  VIDYAVERIFY AI Institutional Intelligence Assistant
                </h3>
                <p className="text-xs text-slate-400 max-w-md mt-1">
                  Ask compliance questions about intake capacities, validation discrepancies, risk calculations, or audit logs.
                </p>
              </div>

              {/* Sample Queries */}
              <div className="w-full max-w-xl text-left pt-2">
                <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2.5 flex items-center gap-1">
                  <HelpCircle size={13} /> Suggested Inquiries:
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {predefinedPrompts.map((prompt) => (
                    <button
                      key={prompt}
                      onClick={() => handleSend(prompt)}
                      className="p-2.5 text-left text-xs rounded-lg border border-slate-800 bg-slate-950/70 hover:border-cyan-500/40 hover:bg-slate-900 transition-all text-slate-300 hover:text-cyan-300 font-medium"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            messages.map((m) => {
              const isUser = m.sender === "user";
              return (
                <div
                  key={m.id}
                  className={`flex flex-col ${isUser ? "items-end" : "items-start"} space-y-1`}
                >
                  <div className="flex items-center gap-1.5 px-1 text-[11px] text-slate-500">
                    <span>{isUser ? "You" : "Compliance Copilot"}</span>
                    <span>•</span>
                    <span>{m.timestamp}</span>
                  </div>

                  <div
                    className={`max-w-[85%] rounded-2xl px-4 py-3 text-xs leading-relaxed ${
                      isUser
                        ? "bg-cyan-600 text-white rounded-tr-sm shadow-md shadow-cyan-950/30"
                        : "bg-slate-950 border border-slate-800 text-slate-200 rounded-tl-sm shadow-md"
                    }`}
                  >
                    <div className="whitespace-pre-wrap">{m.text}</div>

                    {!isUser && m.responseMeta && (
                      <div className="mt-3 pt-2.5 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-2 text-[10px]">
                        <div className="flex items-center gap-2">
                          <span
                            className={`px-2 py-0.5 rounded font-mono font-semibold ${
                              m.responseMeta.is_llm
                                ? "bg-emerald-500/15 border border-emerald-500/30 text-emerald-400"
                                : "bg-cyan-500/15 border border-cyan-500/30 text-cyan-400"
                            }`}
                          >
                            {m.responseMeta.is_llm ? "LLM Mode" : "Deterministic Fallback"}
                          </span>
                          <span className="text-slate-400 font-mono">
                            {m.responseMeta.provider}
                          </span>
                        </div>

                        {m.responseMeta.evidence_refs && m.responseMeta.evidence_refs.length > 0 && (
                          <span className="text-slate-400 font-mono">
                            {m.responseMeta.evidence_refs.length} record(s) cited
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Follow-up suggested questions */}
                  {!isUser && m.responseMeta?.suggested_questions && (
                    <div className="flex flex-wrap gap-1.5 mt-2 max-w-[85%]">
                      {m.responseMeta.suggested_questions.map((sq, idx) => (
                        <button
                          key={idx}
                          onClick={() => handleSend(sq)}
                          className="px-2.5 py-1 text-[11px] rounded-lg bg-slate-950 border border-slate-800 hover:border-cyan-500/40 text-slate-400 hover:text-cyan-300 transition-colors"
                        >
                          → {sq}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              );
            })
          )}

          {loading && (
            <div className="flex flex-col items-start space-y-1">
              <span className="px-1 text-[11px] text-slate-500">Compliance Copilot is retrieving data...</span>
              <div className="px-4 py-3 rounded-2xl rounded-tl-sm bg-slate-950 border border-slate-800 text-xs text-cyan-400 flex items-center gap-2">
                <RefreshCw size={13} className="animate-spin" />
                <span>Executing authorized database query tool...</span>
              </div>
            </div>
          )}
        </div>

        {/* Input Bar & Error Notification */}
        <div className="border-t border-slate-800 p-3 bg-slate-950/80 space-y-2">
          {error && (
            <div className="p-2.5 rounded-lg border border-rose-500/30 bg-rose-500/10 text-rose-400 text-xs flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertCircle size={15} />
                <span>{error}</span>
              </div>
              {retryQuery && (
                <button
                  onClick={() => handleSend(retryQuery)}
                  className="px-2 py-0.5 rounded bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 font-semibold text-[11px] flex items-center gap-1"
                >
                  <RefreshCw size={11} /> Retry
                </button>
              )}
            </div>
          )}

          <div className="flex gap-2 items-end">
            <textarea
              ref={textareaRef}
              rows={1}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
              placeholder="Ask a compliance question... (Press Enter to send, Shift+Enter for newline)"
              className="flex-1 px-3.5 py-2.5 rounded-xl text-xs bg-slate-900 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 resize-none max-h-32 disabled:opacity-50"
            />
            <button
              onClick={() => handleSend()}
              disabled={loading || !question.trim()}
              className="px-4 py-2.5 rounded-xl font-semibold text-xs text-slate-950 bg-cyan-500 hover:bg-cyan-400 disabled:opacity-40 transition-colors flex items-center gap-1.5 shadow-sm shrink-0"
              title="Send message"
            >
              <Send size={15} />
              <span className="hidden sm:inline">Ask</span>
            </button>
          </div>
          <p className="text-[10px] text-slate-500 text-right">
            VIDYAVERIFY AI Copilot v2.0 • Model answers grounded in PostgreSQL 16
          </p>
        </div>
      </Card>
    </div>
  );
}
