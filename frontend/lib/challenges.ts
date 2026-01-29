import { apiFetch } from "./api";

export type Challenge = {
  challenge_id: number;
  prompt: string;
};

export type TutorResult = {
  score: number;
  pass_node: boolean;
  feedback_summary: string;
  suggestions: string[];
};

export async function getOrCreateChallenge(
  pathId: number,
  nodeId: number
): Promise<Challenge> {
  return apiFetch(
    `/api/paths/${pathId}/nodes/${nodeId}/challenges`,
    {
      method: "POST",
    }
  );
}

export async function submitChallenge(
  challengeId: number,
  answer: string
): Promise<TutorResult> {
  return apiFetch(`/api/challenges/${challengeId}/submit`, {
    method: "POST",
    body: JSON.stringify({ answer }),
  });
}
