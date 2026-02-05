"use client";

import React, { useMemo } from "react";
import { PathProgress } from "@/lib/paths";

type FullPathNode = {
  id: number;
  title: string;
  description: string;
  node_type: string;
  estimated_minutes?: number;
  metadata_json?: any;
};

type FullPathEdge = {
  from_node_id: number;
  to_node_id: number;
};

interface FullPathPanelProps {
  nodes: FullPathNode[];
  edges: FullPathEdge[];
  progress: PathProgress | null;
}

const statusStyles: Record<string, string> = {
  completed: "bg-green-100 text-green-700",
  in_progress: "bg-blue-100 text-blue-700",
  blocked: "bg-gray-200 text-gray-700",
  not_started: "bg-slate-100 text-slate-700",
};

const typeStyles: Record<string, string> = {
  concept: "bg-indigo-100 text-indigo-700",
  skill: "bg-amber-100 text-amber-700",
  project: "bg-emerald-100 text-emerald-700",
  meta: "bg-purple-100 text-purple-700",
  remedial: "bg-rose-100 text-rose-700",
};

const FullPathPanel: React.FC<FullPathPanelProps> = ({ nodes, edges, progress }) => {
  const { progressMap, prereqsMap } = useMemo(() => {
    const map: Record<number, { status: string }> = {};
    if (progress) {
      for (const p of progress.nodes) {
        map[p.node_id] = { status: p.status };
      }
    }
    const prereqs: Record<number, number[]> = {};
    for (const edge of edges) {
      if (!prereqs[edge.to_node_id]) {
        prereqs[edge.to_node_id] = [];
      }
      prereqs[edge.to_node_id].push(edge.from_node_id);
    }

    return { progressMap: map, prereqsMap: prereqs };
  }, [progress, edges]);

  const computeStatus = (nodeId: number): string => {
    const prereqs = prereqsMap[nodeId] || [];
    if (prereqs.length > 0) {
      const blocked = prereqs.some(
        (pid) => progressMap[pid]?.status !== "completed"
      );
      if (blocked) return "blocked";
    }
    return progressMap[nodeId]?.status || "not_started";
  };

  return (
    <div>
      <div className="mb-3">
        <h3 className="text-lg font-semibold text-gray-900">Full Learning Path</h3>
        <p className="text-sm text-muted">
          Read the full curriculum in order. Status updates based on your progress.
        </p>
      </div>

      <div className="space-y-3 max-h-[70vh] overflow-y-auto pr-2">
        {nodes.map((node) => {
          const status = computeStatus(node.id);
          const statusClass = statusStyles[status] || statusStyles.not_started;
          const typeClass = typeStyles[node.node_type] || "bg-slate-100 text-slate-700";
          return (
            <div
              key={node.id}
              className="border rounded-lg p-4 bg-white shadow-sm hover:shadow-md transition"
            >
              <div className="flex items-center justify-between gap-3">
                <h4 className="text-base font-semibold text-gray-900">{node.title}</h4>
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-1 rounded text-xs font-semibold ${typeClass}`}>
                    {node.node_type}
                  </span>
                  <span className={`px-2 py-1 rounded text-xs font-semibold ${statusClass}`}>
                    {status.replace("_", " ")}
                  </span>
                </div>
              </div>

              <p className="text-sm text-gray-700 mt-2 leading-relaxed">
                {node.description}
              </p>

              <div className="mt-3 flex items-center gap-3 text-xs text-gray-500">
                <span>
                  Est. {node.estimated_minutes ? `${node.estimated_minutes} min` : "time TBD"}
                </span>
                {Array.isArray(node.metadata_json?.tags) && node.metadata_json.tags.length > 0 && (
                  <span>
                    Tags: {node.metadata_json.tags.slice(0, 3).join(", ")}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default FullPathPanel;
