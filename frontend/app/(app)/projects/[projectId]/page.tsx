"use client";

import { useEffect, useState } from "react";
import { fetchProject } from "@/lib/paths";
import {
  getOrCreateChallenge,
  submitChallenge,
  Challenge,
  TutorResult,
} from "@/lib/challenges";

export default function ProjectDetailPage({
  params,
}: {
  params: { projectId: string };
}) {
  const [project, setProject] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const [activeNode, setActiveNode] = useState<any>(null);
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [answer, setAnswer] = useState("");
  const [tutorResult, setTutorResult] = useState<TutorResult | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    fetchProject(params.projectId)
      .then(setProject)
      .finally(() => setLoading(false));
  }, [params.projectId]);

  async function startChallenge(node: any) {
    setBusy(true);
    setActiveNode(node);
    setTutorResult(null);
    setAnswer("");

    const ch = await getOrCreateChallenge(
      Number(params.projectId),
      node.id
    );

    setChallenge(ch);
    setBusy(false);
  }

  async function submitAnswer() {
    if (!challenge) return;

    setBusy(true);
    const result = await submitChallenge(challenge.challenge_id, answer);
    setTutorResult(result);
    setBusy(false);
  }

  if (loading) return <div className="p-6">Loading…</div>;
  if (!project) return <div className="p-6">Not found</div>;

  return (
    <div className="max-w-5xl mx-auto p-6">
      <h1 className="text-2xl font-semibold">{project.goal_title}</h1>
      <p className="text-gray-600 mt-2 mb-6">{project.summary}</p>

      {/* Nodes list */}
      <div className="space-y-4">
        {project.nodes.map((node: any, idx: number) => (
          <div
            key={node.id}
            className="border rounded p-4 flex justify-between"
          >
            <div>
              <h3 className="font-medium">
                {idx + 1}. {node.title}
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                {node.description}
              </p>
            </div>

            <button
              onClick={() => startChallenge(node)}
              disabled={busy}
              className="text-sm px-3 py-1 rounded border hover:bg-gray-50"
            >
              Take Challenge
            </button>
          </div>
        ))}
      </div>

      {/* Challenge panel */}
      {challenge && (
        <div className="mt-8 border rounded p-6 bg-white">
          <h2 className="font-semibold mb-2">
            Challenge: {activeNode?.title}
          </h2>

          <p className="mb-4 whitespace-pre-wrap">
            {challenge.prompt}
          </p>

          {!tutorResult && (
            <>
              <textarea
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                className="w-full border rounded p-3 mb-4"
                rows={6}
                placeholder="Write your answer here…"
              />

              <button
                onClick={submitAnswer}
                disabled={busy || !answer}
                className="bg-pink-600 text-white px-4 py-2 rounded"
              >
                {busy ? "Submitting…" : "Submit Answer"}
              </button>
            </>
          )}

          {/* Tutor feedback */}
          {tutorResult && (
            <div className="mt-4">
              <p className="font-medium">
                Score: {Math.round(tutorResult.score * 100)}%
              </p>

              <p className="mt-2">
                {tutorResult.pass_node
                  ? "You passed this node"
                  : "You should retry this node"}
              </p>

              <p className="mt-3 text-gray-700">
                {tutorResult.feedback_summary}
              </p>

              {tutorResult.suggestions.length > 0 && (
                <ul className="mt-3 list-disc pl-5 text-sm">
                  {tutorResult.suggestions.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
