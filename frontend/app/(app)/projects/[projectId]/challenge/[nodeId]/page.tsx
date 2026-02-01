"use client";

import { useEffect, useState } from "react";
import {
  getOrCreateChallenge,
  submitChallenge,
  getHint,
  Challenge,
  TutorResult,
  Hint,
} from "@/lib/challenges";
import { fetchPathProgress } from "@/lib/paths";
import Link from 'next/link';
import TutorHint from "@/components/challenge/TutorHint";

export default function ChallengePage({
  params,
}: {
  params: { projectId: string; nodeId: string };
}) {
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [answer, setAnswer] = useState("");
  const [tutorResult, setTutorResult] = useState<TutorResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  
  // Hint-related state
  const [hints, setHints] = useState<string[]>([]);
  const [hintLevel, setHintLevel] = useState(0);
  const [isRequestingHint, setIsRequestingHint] = useState(false);

  useEffect(() => {
    async function loadChallenge() {
      setLoading(true);
      try {
        const ch = await getOrCreateChallenge(
          Number(params.projectId),
          Number(params.nodeId)
        );
        setChallenge(ch);
      } catch (error) {
        console.error("Failed to load challenge:", error);
      } finally {
        setLoading(false);
      }
    }
    loadChallenge();
  }, [params.projectId, params.nodeId]);

  async function submitAnswer() {
    if (!challenge) return;

    setBusy(true);
    try {
      const result = await submitChallenge(challenge.challenge_id, answer);
      setTutorResult(result);
      // Optionally refresh progress in the background if needed elsewhere
      fetchPathProgress(params.projectId);
    } catch (error) {
      console.error("Failed to submit answer:", error);
    } finally {
      setBusy(false);
    }
  }

  async function handleGetHint() {
    if (!challenge) return;

    setIsRequestingHint(true);
    try {
        const newHint = await getHint(challenge.challenge_id, hintLevel);
        setHints([...hints, newHint.hint]);
        setHintLevel(hintLevel + 1);
    } catch (error) {
        console.error("Failed to get hint:", error);
        // Optionally, show an error to the user
    } finally {
        setIsRequestingHint(false);
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="loader ease-linear rounded-full border-4 border-t-4 border-gray-200 h-12 w-12 animate-spin" style={{ borderColor: 'var(--border)', borderTopColor: 'var(--accent)' }}></div>
      </div>
    );
  }

  if (!challenge) {
    return (
      <div className="text-center p-8">
        <h2 className="text-2xl font-bold text-red-600">Failed to Load Challenge</h2>
        <p className="text-muted mt-2">There was an error fetching the challenge. Please try again.</p>
        <Link href={`/projects/${params.projectId}`} className="mt-4 inline-block bg-accent text-white font-bold py-2 px-4 rounded">
            Go Back to Project
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto p-8">
        <div className="p-8 bg-white rounded-lg shadow-lg border border-border">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Challenge
          </h1>
          <p className="text-muted mb-6">Prove your understanding to complete this node.</p>

          <div className="mb-6 bg-gray-50 p-4 rounded-md border">
            <p className="whitespace-pre-wrap text-gray-800">
                {challenge.prompt}
            </p>
          </div>

          {!tutorResult && (
            <>
              <div className="flex flex-col md:flex-row gap-4">
                <textarea
                    value={answer}
                    onChange={(e) => setAnswer(e.target.value)}
                    className="w-full border rounded p-3 mb-4 focus:outline-none focus:shadow-outline focus:border-accent"
                    rows={8}
                    placeholder="Write your answer here…"
                    disabled={busy}
                />
                <div className="flex flex-col gap-2">
                    <button
                        onClick={handleGetHint}
                        disabled={isRequestingHint || busy}
                        className={`w-full md:w-auto bg-blue-500 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline transition duration-200 ease-in-out hover:bg-blue-600 ${isRequestingHint || busy ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                        {isRequestingHint ? "Thinking..." : "Get a Hint"}
                    </button>
                </div>
              </div>
              <button
                onClick={submitAnswer}
                disabled={busy || !answer}
                className={`w-full mt-4 bg-accent text-white font-bold py-3 px-4 rounded focus:outline-none focus:shadow-outline transition duration-200 ease-in-out hover:bg-pink-700 ${busy || !answer ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                {busy ? "Submitting…" : "Submit Answer"}
              </button>
            </>
          )}

          {hints.map((hint, index) => (
            <TutorHint key={index} hint={hint} level={index + 1} />
          ))}

          {tutorResult && (
            <div className="mt-4">
              <h2 className="text-2xl font-semibold">Feedback</h2>
              <p className="font-medium text-lg mt-2">
                Score: {Math.round(tutorResult.score * 100)}%
              </p>

              <p className={`mt-2 font-semibold ${tutorResult.pass_node ? 'text-green-600' : 'text-red-600'}`}>
                {tutorResult.pass_node
                  ? "Congratulations! You passed this node."
                  : "Not quite. You should review the feedback and try again."}
              </p>

              <p className="mt-4 text-gray-700 bg-gray-50 p-4 rounded border">
                {tutorResult.feedback_summary}
              </p>

              {tutorResult.suggestions.length > 0 && (
                <div className="mt-4">
                    <h3 className="font-semibold">Suggestions for Improvement:</h3>
                    <ul className="mt-2 list-disc pl-5 text-sm text-muted">
                    {tutorResult.suggestions.map((s, i) => (
                        <li key={i}>{s}</li>
                    ))}
                    </ul>
                </div>
              )}

              <div className="flex gap-4 mt-6">
                {!tutorResult.pass_node && (
                    <button
                    onClick={() => {
                        setTutorResult(null);
                        setAnswer("");
                        setHints([]); // Also reset hints on retry
                        setHintLevel(0);
                    }}
                    className="flex-1 bg-accent hover:bg-pink-700 text-white font-bold py-3 px-4 rounded focus:outline-none focus:shadow-outline transition duration-200 ease-in-out"
                    >
                    Retry Challenge
                    </button>
                )}
                <Link href={`/projects/${params.projectId}?refreshed=true`} className="flex-1 text-center bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-3 px-4 rounded focus:outline-none focus:shadow-outline transition duration-200 ease-in-out">
                    Back to Learning Path
                </Link>
              </div>
            </div>
          )}
        </div>
    </div>
  );
}
