"use client";

import React from 'react';
import { Node } from 'reactflow';
import { useRouter } from 'next/navigation';

interface NodeDetailsPanelProps {
  node: Node | null;
  projectId: string;
  currentNodeCount: number;
}

const NodeDetailsPanel: React.FC<NodeDetailsPanelProps> = ({ node, projectId, currentNodeCount }) => {
  const router = useRouter();

  if (!node) {
    return (
      <div className="p-8 bg-white rounded-lg shadow-lg border border-border">
        <h3 className="text-xl font-bold text-gray-900">Select a Node</h3>
        <p className="text-muted mt-2">Click on a node in the graph to see its details.</p>
      </div>
    );
  }

  const handleStartChallenge = () => {
    // Store the current node count before navigating away.
    sessionStorage.setItem(`nodeCount_${projectId}`, currentNodeCount.toString());
    router.push(`/projects/${projectId}/challenge/${node.id}`);
  }

  const isLocked = node.data.status === 'blocked';

  return (
    <div className="p-8 bg-white rounded-lg shadow-lg border border-border">
      <h3 className="text-2xl font-bold text-gray-900 mb-4">{node.data.label}</h3>
      
      <div className="space-y-4">
        <div>
          <h4 className="font-semibold text-gray-700">Description</h4>
          <p className="text-muted">{node.data.description || 'No description available.'}</p>
        </div>
        
        <div>
          <h4 className="font-semibold text-gray-700">Estimated Time</h4>
          <p className="text-muted">{node.data.estimated_minutes ? `${node.data.estimated_minutes} minutes` : 'Not specified.'}</p>
        </div>

        <div>
          <h4 className="font-semibold text-gray-700">Status</h4>
          <p className={`capitalize font-medium ${
            node.data.status === 'completed' ? 'text-green-600' : 
            node.data.status === 'in_progress' ? 'text-blue-600' :
            'text-muted'
          }`}>
            {node.data.status ? node.data.status.replace('_', ' ') : 'Not Started'}
          </p>
        </div>
        
        <button 
          onClick={handleStartChallenge}
          disabled={isLocked}
          title={isLocked ? "Complete prerequisite nodes first." : "Start this challenge"}
          className={`w-full mt-4 bg-accent text-white font-bold py-3 px-4 rounded focus:outline-none focus:shadow-outline transition duration-200 ease-in-out hover:bg-pink-700 ${isLocked ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          {isLocked ? 'Locked' : 'Start Challenge'}
        </button>
      </div>
    </div>
  );
};

export default NodeDetailsPanel;
