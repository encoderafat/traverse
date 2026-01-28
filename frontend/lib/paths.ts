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
