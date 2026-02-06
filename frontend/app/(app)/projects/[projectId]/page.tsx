"use client";

import { useEffect, useState, useMemo } from "react";
import { useSearchParams, useParams, useRouter } from 'next/navigation';
import { fetchProject, fetchPathProgress, PathProgress, updateNodeStatus } from "@/lib/paths";
import DagView from "@/components/dag/DagView";
import NodeDetailsPanel from "@/components/dag/NodeDetailsPanel";
import FullPathPanel from "@/components/dag/FullPathPanel";
import Notification from "@/components/ui/Notification";
import { Node, Edge, MarkerType } from "reactflow";

// Helper function to perform a simple layout
const getLayoutedElements = (
  nodes: any[],
  edges: any[],
  progress: PathProgress | null,
  onStartChallenge: (nodeId: string) => void,
  onMarkComplete: (nodeId: string, status: 'completed') => void
) => {
  const isNodeLocked = (nodeId: number, progressMap: any, allEdges: any[]): boolean => {
    const prereqs = allEdges
      .filter((e) => e.to_node_id === nodeId)
      .map((e) => e.from_node_id);

    if (prereqs.length === 0) return false;
    return prereqs.some((pid) => progressMap[pid]?.status !== "completed");
  };

  const progressMap = progress
    ? Object.fromEntries(progress.nodes.map((p: any) => [p.node_id, p]))
    : {};

  const layoutedNodes: Node[] = nodes.map((node, i) => {
    const nodeProgress = progressMap[node.id];
    const locked = isNodeLocked(node.id, progressMap, edges);
    const status = locked ? 'blocked' : (nodeProgress?.status || 'not_started');

    return {
      id: node.id.toString(),
      type: "dagNode",
      data: {
        label: node.title,
        description: node.description,
        estimated_minutes: node.estimated_minutes,
        status: status,
       },
      position: { x: (i % 4) * 250, y: Math.floor(i / 4) * 150 },
      style: {
        background: 'transparent',
        border: 'none',
      },
      draggable: false, // For a cleaner UI
    };
  });

  const layoutedEdges: Edge[] = edges.map((edge) => {
    const targetLocked = isNodeLocked(edge.to_node_id, progressMap, edges);
    const strokeColor = targetLocked ? '#94A3B8' : 'var(--accent)';
    return {
      id: `e${edge.from_node_id}-${edge.to_node_id}`,
      source: edge.from_node_id.toString(),
      target: edge.to_node_id.toString(),
      animated: !targetLocked,
      style: {
        stroke: strokeColor,
        strokeWidth: 2,
        strokeDasharray: targetLocked ? '6 4' : undefined,
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: strokeColor,
      },
    };
  });

  return { layoutedNodes, layoutedEdges };
};


export default function ProjectDetailPage() {
  const [project, setProject] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [progress, setProgress] = useState<PathProgress | null>(null);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [activeTab, setActiveTab] = useState<"details" | "full">("details");

  // Notification State
  const [showNotification, setShowNotification] = useState(false);
  const [notificationMessage, setNotificationMessage] = useState("");

  const searchParams = useSearchParams();
  const params = useParams();
  const router = useRouter();
  const { projectId } = params;

  useEffect(() => {
    if (!projectId) {
      setLoading(false);
      return;
    }

    Promise.all([
      fetchProject(projectId as string),
      fetchPathProgress(projectId as string),
    ])
      .then(([proj, prog]) => {
        setProject(proj);
        setProgress(prog);

        // Check for adaptation after data is fetched
        const refreshed = searchParams.get('refreshed');
        if (refreshed === 'true') {
          const storageKey = `nodeCount_${projectId}`;
          const storedValue = sessionStorage.getItem(storageKey);
          if (storedValue !== null) {
            const oldNodeCount = parseInt(storedValue, 10);
            const newNodeCount = proj.nodes.length;
            if (Number.isFinite(oldNodeCount) && newNodeCount > oldNodeCount) {
              setNotificationMessage("Your path was updated! We added a new prerequisite node to help you master this topic.");
              setShowNotification(true);
            }
            // Clean up sessionStorage only when we had a stored value
            sessionStorage.removeItem(storageKey);
          }
          // Remove the query param to avoid repeated notifications on refresh
          router.replace(`/projects/${projectId}`);
        }
      })
      .finally(() => setLoading(false));
  }, [projectId, searchParams]);

  const handleUpdateNodeStatus = async (nodeId: string, status: 'completed') => {
    if (!projectId) return;

    // Optimistic UI update
    const numericNodeId = parseInt(nodeId, 10);
    if (progress) {
      const newNodes = progress.nodes.map(n => 
        n.node_id === numericNodeId ? { ...n, status } : n
      );
      setProgress({ ...progress, nodes: newNodes });
    }
    if (selectedNode) {
      setSelectedNode({ ...selectedNode, data: { ...selectedNode.data, status }});
    }

    try {
      await updateNodeStatus(projectId as string, nodeId, status);
      // Refetch the progress to ensure data consistency
      const updatedProgress = await fetchPathProgress(projectId as string);
      setProgress(updatedProgress);
    } catch (error) {
      console.error("Failed to update node status:", error);
      // Optionally, revert the optimistic update here
      // For now, we just log the error
    }
  };

  const handleNodeClick = (_event: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
    setActiveTab("details");
  };

  const handleStartChallenge = (nodeId: string) => {
    if (!projectId) return;
    sessionStorage.setItem(`nodeCount_${projectId}`, project.nodes.length.toString());
    router.push(`/projects/${projectId}/challenge/${nodeId}`);
  };

  const { layoutedNodes, layoutedEdges } = useMemo(() => {
    if (!project) return { layoutedNodes: [], layoutedEdges: [] };
    return getLayoutedElements(
      project.nodes,
      project.edges,
      progress,
      handleStartChallenge,
      handleUpdateNodeStatus
    );
  }, [project, progress, handleStartChallenge, handleUpdateNodeStatus]);

  if (loading) return <div className="p-6 text-center text-muted">Loading learning path…</div>;
  if (!project) return <div className="p-6 text-center text-muted">Learning path not found.</div>;

  return (
    <div className="max-w-7xl mx-auto p-6">
      {showNotification && (
        <Notification
          message={notificationMessage}
          type="info"
          onClose={() => setShowNotification(false)}
        />
      )}
      <h1 className="text-4xl font-semibold heading-font text-primary">{project.goal_title}</h1>
      <p className="text-muted mt-2 mb-6">{project.summary}</p>

      {progress && (
        <div className="mb-6">
          <div className="flex justify-between text-sm mb-1">
            <span className="font-semibold">Overall Progress</span>
            <span className="font-semibold">{Math.round(progress.completion_ratio * 100)}%</span>
          </div>
          <div className="w-full h-3 bg-surface-alt rounded-full border border-border">
            <div
              className="h-3 rounded-full"
              style={{
                width: `${progress.completion_ratio * 100}%`,
                backgroundColor: 'var(--accent)',
              }}
            />
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-[1.6fr_1fr] gap-6 items-start">
        <div className="card p-4">
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-slate-900">Learning Graph</h2>
            <p className="text-sm text-muted">Click a node to view details or start a challenge.</p>
            <div className="mt-3 flex flex-wrap gap-2 text-xs">
              <span className="pill bg-green-100 text-green-700">completed</span>
              <span className="pill bg-sky-100 text-sky-700">in progress</span>
              <span className="pill bg-sky-50 text-sky-700">ready</span>
              <span className="pill bg-slate-200 text-slate-700">blocked</span>
            </div>
          </div>
          <DagView initialNodes={layoutedNodes} initialEdges={layoutedEdges} onNodeClick={handleNodeClick} />
        </div>

        <div className="card p-4">
          <div className="flex gap-2 mb-4">
            <button
              onClick={() => setActiveTab("details")}
              className={`px-4 py-2 rounded text-sm font-semibold transition ${
                activeTab === "details"
                  ? "bg-accent text-white"
                  : "bg-surface-alt text-slate-700 hover:bg-slate-200"
              }`}
            >
              Details
            </button>
            <button
              onClick={() => setActiveTab("full")}
              className={`px-4 py-2 rounded text-sm font-semibold transition ${
                activeTab === "full"
                  ? "bg-accent text-white"
                  : "bg-surface-alt text-slate-700 hover:bg-slate-200"
              }`}
            >
              Full Path
            </button>
          </div>

          {activeTab === "details" ? (
            <NodeDetailsPanel
              node={selectedNode}
              projectId={projectId as string}
              currentNodeCount={project.nodes.length}
              onUpdateNodeStatus={handleUpdateNodeStatus}
            />
          ) : (
            <FullPathPanel
              nodes={project.nodes}
              edges={project.edges}
              progress={progress}
            />
          )}
        </div>
      </div>
    </div>
  );
}
