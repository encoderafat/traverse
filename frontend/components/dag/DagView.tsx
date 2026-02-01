"use client";

import React, { useState, useCallback, useEffect } from 'react';
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
} from 'reactflow';

// Import React Flow styles
import 'reactflow/dist/style.css';

interface DagViewProps {
  initialNodes: Node[];
  initialEdges: Edge[];
  onNodeClick: (_event: React.MouseEvent, node: Node) => void;
}

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

  return (
    <div style={{ height: '70vh', border: '1px solid var(--border)', borderRadius: '8px' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={handleNodeClick}
        fitView
      >
        <Controls />
        <Background />
      </ReactFlow>
    </div>
  );
};

export default DagView;
