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

export type Hint = {
    hint: string;
}

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

// Mock function for getting hints
export async function getHint(
    challengeId: number,
    hintLevel: number
): Promise<Hint> {
    console.log(`Fetching hint for challenge ${challengeId} at level ${hintLevel}`);
    
    // In a real implementation, this would be:
    // return apiFetch(`/api/challenges/${challengeId}/hint`, {
    //   method: "POST",
    //   body: JSON.stringify({ hintLevel }),
    // });

    const mockHints = [
        "Think about the initial state of the system. What are the key assumptions?",
        "Consider the error message carefully. What specific part of the code is it pointing to?",
        "Have you checked the documentation for the library function you're using? There might be a common pitfall.",
        "Try to isolate the problem. Can you create a smaller, reproducible example?",
    ];

    return new Promise((resolve) => {
        setTimeout(() => {
            resolve({
                hint: mockHints[hintLevel] || "I'm out of hints for now. Try to consolidate what you've learned and approach the problem from a new angle."
            });
        }, 800); // Simulate network delay
    });
}
