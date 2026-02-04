"use client";

import React, { useState } from 'react';
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
  const [isMenuOpen, setIsMenuOpen] = useState(false);

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

  const handleMarkAsComplete = () => {
    onUpdateNodeStatus(node.id, 'completed');
    setIsMenuOpen(false);
  }

  const isLocked = node.data.status === 'blocked';
  const isCompleted = node.data.status === 'completed';

  return (
    <div className="p-8 bg-white rounded-lg shadow-lg border border-border">
      <div className="flex justify-between items-start">
        <h3 className="text-2xl font-bold text-gray-900 mb-4">{node.data.label}</h3>
        <div className="relative">
          <button 
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="p-2 rounded-md hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-500"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
            </svg>
          </button>
          {isMenuOpen && (
            <div className="absolute right-0 mt-2 w-56 bg-white rounded-md shadow-lg border z-10">
              <ul className="py-1">
                <li>
                  <button
                    onClick={handleStartChallenge}
                    disabled={isLocked}
                    title={isLocked ? "Complete prerequisite nodes first." : "Start this challenge"}
                    className={`w-full text-left flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 ${isLocked ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.536L16.732 3.732z" /></svg>
                    {isCompleted ? 'Review Challenge' : 'Start Challenge'}
                  </button>
                </li>
                <li>
                  <button
                    onClick={handleMarkAsComplete}
                    disabled={isCompleted || isLocked}
                    title={isCompleted ? "Node is already completed." : (isLocked ? "Cannot mark a locked node as complete." : "Mark this node as complete")}
                    className={`w-full text-left flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 ${isCompleted || isLocked ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                    Mark as Complete
                  </button>
                </li>
              </ul>
            </div>
          )}
        </div>
      </div>
      
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
      </div>
    </div>
  );
};

export default NodeDetailsPanel;
