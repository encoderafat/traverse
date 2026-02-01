// lib/paths.ts
import { apiFetch } from "./api";

export interface LearningPath {
  id: number;
  goal_title: string;
  summary: string;
  goal_description?: string; // Added from original payload
  domain_hint?: string;     // Added from original payload
  level?: string;           // Added from original payload
  user_background?: string; // Added from original payload
}

export async function fetchPaths(): Promise<LearningPath[]> {
  return apiFetch("/api/paths");
}

export async function createPath(payload: {
  goal_title: string;
  goal_description?: string;
  domain_hint?: string;
  level?: string;
  user_background?: string;
}): Promise<LearningPath> { // Ensure it returns a LearningPath
  return apiFetch<LearningPath>("/api/paths", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchProject(projectId: string) {
  // Renamed to fetchPath for consistency, but kept fetchProject for now
  // to avoid breaking other parts of the app if they use it.
  // Ideally, this should also return LearningPath
  return apiFetch<{
    id: number;
    goal_title: string;
    summary: string;
    nodes: {
      id: number;
      title: string;
      description: string;
      node_type: string;
      estimated_minutes?: number;
      metadata_json?: any;
    }[];
    edges: {
      from_node_id: number;
      to_node_id: number;
    }[];
  }>(`/api/paths/${projectId}`);
}

export type NodeProgress = {
  node_id: number;
  title: string;
  status: "not_started" | "in_progress" | "completed" | "blocked";
  last_score: number | null;
  attempts_count: number;
};

export type PathProgress = {
  path_id: number;
  completion_ratio: number; // 0..1
  nodes: NodeProgress[];
};

export async function fetchPathProgress(
  projectId: string
): Promise<PathProgress> {
  return apiFetch(`/api/paths/${projectId}/progress`);
}

