"use client";

import { useEffect, useState, useCallback } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  type Node,
  type Edge,
  type OnNodesChange,
  type OnEdgesChange,
  applyNodeChanges,
  applyEdgeChanges,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { AppShell } from "@/components/AppShell";
import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";

const nodeColors: Record<string, string> = {
  institution: "#3b82f6",
  course: "#8b5cf6",
  student: "#06b6d4",
  submission: "#22c55e",
  issue: "#f97316",
  risk: "#ef4444",
  case: "#eab308",
  approval: "#6366f1",
};

export default function GraphPage() {
  return (
    <AppShell>
      <GraphView />
    </AppShell>
  );
}

function GraphView() {
  const [institutions, setInstitutions] = useState<any[]>([]);
  const [selectedInst, setSelectedInst] = useState("");
  const [loading, setLoading] = useState(true);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);

  useEffect(() => {
    api.get("/institutions?page=1&page_size=100").then((d: any) => setInstitutions(d.items)).catch(() => {});
  }, []);

  const loadGraph = useCallback(async () => {
    setLoading(true);
    const params = new URLSearchParams();
    if (selectedInst) params.set("institution_id", selectedInst);
    try {
      const data = await api.get<any>(`/graph?${params}`);
      const rNodes: Node[] = data.nodes.map((n: any, i: number) => ({
        id: n.id,
        type: "default",
        position: {
          x: 150 + (i % 6) * 180,
          y: 80 + Math.floor(i / 6) * 120,
        },
        data: { label: n.data.label },
        style: {
          background: `${nodeColors[n.type] || "#64748b"}20`,
          border: `1px solid ${nodeColors[n.type] || "#64748b"}`,
          color: nodeColors[n.type] || "#64748b",
          borderRadius: 8,
          fontSize: 11,
          padding: 4,
        },
      }));
      // Deduplicate edges by ID to avoid React key conflicts
      const seenEdgeIds = new Set<string>();
      const rEdges: Edge[] = data.edges
        .filter((e: any) => {
          if (seenEdgeIds.has(e.id)) return false;
          seenEdgeIds.add(e.id);
          return true;
        })
        .map((e: any) => ({
          id: e.id,
          source: e.source,
          target: e.target,
          label: e.label,
          animated: e.type === "potential_conflict",
          style: e.type === "potential_conflict"
            ? { stroke: "#ef4444", strokeDasharray: 4 }
            : e.type === "approval"
            ? { stroke: "#6366f1" }
            : { stroke: "#475569" },
        }));
      setNodes(rNodes);
      setEdges(rEdges);
    } catch {
    } finally {
      setLoading(false);
    }
  }, [selectedInst]);

  useEffect(() => {
    loadGraph();
  }, []);

  const onNodesChange: OnNodesChange<Node> = useCallback(
    (changes) => setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  );
  const onEdgesChange: OnEdgesChange<Edge> = useCallback(
    (changes) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    []
  );

  return (
    <div className="space-y-4 h-full">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold">Academic Trust Graph</h1>
          <p className="text-sm" style={{ color: "var(--muted)" }}>
            Interactive relationship graph from real database data
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={selectedInst}
            onChange={(e) => {
              setSelectedInst(e.target.value);
            }}
            className="px-3 py-2 rounded-lg text-sm"
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              color: "var(--foreground)",
            }}
          >
            <option value="">All institutions</option>
            {institutions.map((i) => (
              <option key={i.id} value={i.id}>
                {i.name}
              </option>
            ))}
          </select>
          <button
            onClick={loadGraph}
            className="px-3 py-2 rounded-lg text-sm text-white"
            style={{ background: "var(--accent)" }}
          >
            Load
          </button>
        </div>
      </div>

      <Card className="p-0 h-[600px]">
        {loading ? (
          <div
            className="h-full flex items-center justify-center"
            style={{ color: "var(--muted)" }}
          >
            Loading graph...
          </div>
        ) : nodes.length === 0 ? (
          <div
            className="h-full flex items-center justify-center"
            style={{ color: "var(--muted)" }}
          >
            No graph data available
          </div>
        ) : (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            fitView
            proOptions={{ hideAttribution: true }}
          >
            <Background />
            <Controls />
            <MiniMap
              nodeColor={() => "#06b6d4"}
              maskColor="rgba(15, 23, 42, 0.7)"
            />
          </ReactFlow>
        )}
      </Card>

      <div className="flex flex-wrap gap-3">
        {Object.entries(nodeColors).map(([type, color]) => (
          <div
            key={type}
            className="flex items-center gap-1.5 text-xs"
            style={{ color: "var(--muted)" }}
          >
            <div className="w-3 h-3 rounded" style={{ background: color }} />
            <span className="capitalize">{type}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
