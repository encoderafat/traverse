"use client";

import { useEffect, useState, useMemo } from "react";
import { useSearchParams } from 'next/navigation';
import { fetchProject, fetchPathProgress, PathProgress } from "@/lib/paths";
import DagView from "@/components/dag/DagView";
import NodeDetailsPanel from "@/components/dag/NodeDetailsPanel";
import Notification from "@/components/ui/Notification";
import { Node, Edge } from "reactflow";

// Helper function to perform a simple layout
const getLayoutedElements = (nodes: any[], edges: any[], progress: PathProgress | null) => {
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
    
    let backgroundColor = '#A0AEC0'; // gray-500 for blocked/not_started
    if (status === 'completed') backgroundColor = '#48BB78'; // green-500
    if (status === 'in_progress') backgroundColor = '#4299E1'; // blue-500
    
    return {
      id: node.id.toString(),
      data: { 
        label: node.title,
        description: node.description,
        estimated_minutes: node.estimated_minutes,
        status: status,
       },
      position: { x: (i % 4) * 250, y: Math.floor(i / 4) * 150 },
      style: {
        background: backgroundColor,
        color: 'white',
        border: '1px solid #1a202c',
        borderRadius: '8px',
        width: 180,
        padding: '10px',
      },
      draggable: false, // For a cleaner UI
    };
  });

  const layoutedEdges: Edge[] = edges.map((edge) => ({
    id: `e${edge.from_node_id}-${edge.to_node_id}`,
    source: edge.from_node_id.toString(),
    target: edge.to_node_id.toString(),
    animated: true,
    style: { stroke: 'var(--accent)' }
  }));

  return { layoutedNodes, layoutedEdges };
};


export default function ProjectDetailPage({
  params,
}: {
  params: { projectId:string };
}) {
  const [project, setProject] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [progress, setProgress] = useState<PathProgress | null>(null);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  
  // Notification State
  const [showNotification, setShowNotification] = useState(false);
  const [notificationMessage, setNotificationMessage] = useState("");
  
  const searchParams = useSearchParams();

  useEffect(() => {
    Promise.all([
      fetchProject(params.projectId),
      fetchPathProgress(params.projectId),
    ])
      .then(([proj, prog]) => {
        setProject(proj);
        setProgress(prog);

        // Check for adaptation after data is fetched
        const refreshed = searchParams.get('refreshed');
        if (refreshed === 'true') {
          const oldNodeCount = parseInt(sessionStorage.getItem(`nodeCount_${params.projectId}`) || '0', 10);
          const newNodeCount = proj.nodes.length;
          if (newNodeCount > oldNodeCount) {
            setNotificationMessage("Your path was updated! We added a new prerequisite node to help you master this topic.");
            setShowNotification(true);
          }
          // Clean up sessionStorage
          sessionStorage.removeItem(`nodeCount_${params.projectId}`);
        }
      })
      .finally(() => setLoading(false));
  }, [params.projectId, searchParams]);

  const { layoutedNodes, layoutedEdges } = useMemo(() => {
    if (!project) return { layoutedNodes: [], layoutedEdges: [] };
    return getLayoutedElements(project.nodes, project.edges, progress);
  }, [project, progress]);


  const handleNodeClick = (_event: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
  };

  if (loading) return <div className="p-6 text-center">Loading learning path…</div>;
  if (!project) return <div className="p-6 text-center">Learning path not found.</div>;

  return (
    <div className="max-w-7xl mx-auto p-6">
      {showNotification && (
        <Notification 
          message={notificationMessage}
          type="info"
          onClose={() => setShowNotification(false)}
        />
      )}
      <h1 className="text-3xl font-bold">{project.goal_title}</h1>
      <p className="text-muted mt-2 mb-6">{project.summary}</p>
      
      {progress && (
        <div className="mb-6">
          <div className="flex justify-between text-sm mb-1">
            <span className="font-semibold">Overall Progress</span>
            <span className="font-semibold">{Math.round(progress.completion_ratio * 100)}%</span>
          </div>
          <div className="w-full h-3 bg-gray-200 rounded">
            <div
              className="h-3 rounded"
              style={{
                width: `${progress.completion_ratio * 100}%`,
                backgroundColor: 'var(--accent)',
              }}
            />
          </div>
        </div>
      )}

      <DagView initialNodes={layoutedNodes} initialEdges={layoutedEdges} onNodeClick={handleNodeClick} />
      
      <div className="mt-8">
        <NodeDetailsPanel node={selectedNode} projectId={params.projectId} currentNodeCount={project.nodes.length} />
      </div>
    </div>
  );
}
