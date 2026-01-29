// lib/paths.ts
import { apiFetch } from "./api";

export interface LearningPath {
  id: number;
  goal_title: string;
  summary: string;
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
}) {
  return apiFetch("/api/paths", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export type Project = {
  id: number;
  goal_title: string;
  summary: string;
};

export async function fetchProjects(): Promise<Project[]> {
  return apiFetch<Project[]>("/api/paths");
}

export async function createProject(payload: {
  goal_title: string;
  goal_description?: string;
  domain_hint?: string;
  level?: string;
  user_background?: string;
}) {
  return apiFetch<{ id: number }>("/api/paths", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchProject(projectId: string) {
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
