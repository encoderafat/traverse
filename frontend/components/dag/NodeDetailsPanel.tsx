"use client";

import React from 'react';
import { Node } from 'reactflow';
import { useRouter } from 'next/navigation';

interface NodeDetailsPanelProps {
  node: Node | null;
  projectId: string;
  currentNodeCount: number;
  onUpdateNodeStatus: (nodeId: string, status: 'completed') => void;
}

const NodeDetailsPanel: React.FC<NodeDetailsPanelProps> = ({ node, projectId, currentNodeCount, onUpdateNodeStatus }) => {
  const router = useRouter();
  if (!node) {
    return (
      <div className="p-6 bg-surface-alt rounded-xl border border-border">
        <h3 className="text-xl font-semibold heading-font text-primary">Select a Node</h3>
        <p className="text-muted mt-2">Click on a node in the graph to see its details.</p>
      </div>
    );
  }

  const handleStartChallenge = () => {
    // Store the current node count before navigating away.
    sessionStorage.setItem(`nodeCount_${projectId}`, currentNodeCount.toString());
    router.push(`/projects/${projectId}/challenge/${node.id}`);
  }

  const handleMarkAsComplete = () => {
    onUpdateNodeStatus(node.id, 'completed');
  }

  const isLocked = node.data.status === 'blocked';
  const isCompleted = node.data.status === 'completed';

  return (
    <div className="p-6 bg-surface rounded-xl border border-border">
      <div className="flex justify-between items-start gap-4">
        <h3 className="text-2xl font-semibold heading-font text-primary">{node.data.label}</h3>
        <div className="flex items-center gap-2">
          <button
            onClick={handleStartChallenge}
            disabled={isLocked}
            title={isLocked ? "Complete prerequisite nodes first." : "Start this challenge"}
            className={`btn-secondary text-sm ${
              isLocked ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            {isCompleted ? 'Review Challenge' : 'Start Challenge'}
          </button>
          <button
            onClick={handleMarkAsComplete}
            disabled={isCompleted || isLocked}
            title={isCompleted ? "Node is already completed." : (isLocked ? "Cannot mark a locked node as complete." : "Mark this node as complete")}
            className={`btn-primary text-sm ${
              isCompleted || isLocked ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            Mark as Complete
          </button>
        </div>
      </div>
      
      <div className="space-y-4">
        <div>
          <h4 className="font-semibold text-slate-700">Description</h4>
          <p className="text-slate-700 leading-relaxed">{node.data.description || 'No description available.'}</p>
        </div>
        
        <div>
          <h4 className="font-semibold text-slate-700">Estimated Time</h4>
          <p className="text-muted">{node.data.estimated_minutes ? `${node.data.estimated_minutes} minutes` : 'Not specified.'}</p>
        </div>

        <div>
          <h4 className="font-semibold text-slate-700">Status</h4>
          <p className={`capitalize font-medium ${
            node.data.status === 'completed' ? 'text-green-600' : 
            node.data.status === 'in_progress' ? 'text-blue-600' :
            'text-muted'
          }`}>
            {node.data.status ? node.data.status.replace('_', ' ') : 'Not Started'}
          </p>
        </div>
      </div>
    </div>
  );
};

export default NodeDetailsPanel;
