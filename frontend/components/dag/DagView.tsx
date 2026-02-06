"use client";

import React, { useState, useCallback, useEffect, useMemo } from 'react';
import ReactFlow, {
  Controls,
  Background,
  applyNodeChanges,
  applyEdgeChanges,
  Node,
  Edge,
  NodeChange,
  EdgeChange,
  Connection,
  addEdge,
  Viewport,
  Handle,
  Position,
  NodeProps,
} from 'reactflow';

// Import React Flow styles
import 'reactflow/dist/style.css';

type DagNodeData = {
  label: string;
  description?: string;
  estimated_minutes?: number;
  status?: 'completed' | 'in_progress' | 'blocked' | 'not_started';
};

interface DagViewProps {
  initialNodes: Node[];
  initialEdges: Edge[];
  onNodeClick: (_event: React.MouseEvent, node: Node) => void;
}

const statusStyles: Record<string, string> = {
  completed: 'bg-green-100 text-green-700',
  in_progress: 'bg-sky-100 text-sky-700',
  not_started: 'bg-sky-50 text-sky-700',
  blocked: 'bg-slate-200 text-slate-700',
};

const DagNode: React.FC<NodeProps<DagNodeData>> = ({ data }) => {
  const status = data.status || 'not_started';
  const statusClass = statusStyles[status] || statusStyles.not_started;

  return (
    <div className="min-w-[140px] max-w-[180px] rounded-lg border border-slate-300 bg-white shadow-md px-3 py-2 transition hover:shadow-lg hover:-translate-y-0.5">
      <Handle type="target" position={Position.Left} className="!bg-slate-300 !border-0" />
      <div className="flex items-start justify-between gap-2">
        <div className="text-sm font-semibold text-slate-900 leading-snug">{data.label}</div>
        <span className={`pill ${statusClass}`}>{status.replace('_', ' ')}</span>
      </div>
      <Handle type="source" position={Position.Right} className="!bg-slate-300 !border-0" />
    </div>
  );
};

const DagView: React.FC<DagViewProps> = ({ initialNodes, initialEdges, onNodeClick }) => {
  const [nodes, setNodes] = useState<Node[]>(initialNodes);
  const [edges, setEdges] = useState<Edge[]>(initialEdges);

  useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [initialNodes, initialEdges]);

  const onNodesChange = useCallback(
    (changes: NodeChange[]) => setNodes((nds) => applyNodeChanges(changes, nds)),
    [setNodes]
  );
  const onEdgesChange = useCallback(
    (changes: EdgeChange[]) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    [setEdges]
  );
  const onConnect = useCallback(
    (connection: Connection) => setEdges((eds) => addEdge(connection, eds)),
    [setEdges]
  );

  const handleNodeClick = (_event: React.MouseEvent, node: Node) => {
    onNodeClick(_event, node);
  };

  const nodeTypes = useMemo(() => ({ dagNode: DagNode }), []);

  return (
    <div className="bg-surface border border-border rounded-xl" style={{ height: '70vh' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={handleNodeClick}
        nodeTypes={nodeTypes}
        style={{ backgroundColor: "#E8EEF6" }}
        fitView
      >
        <Controls />
        <Background color="#E2E8F0" gap={20} />
      </ReactFlow>
    </div>
  );
};

export default DagView;
