"use client";

import { useEffect, useState } from "react";
import { fetchProject } from "@/lib/paths";
import {
  getOrCreateChallenge,
  submitChallenge,
  Challenge,
  TutorResult,
} from "@/lib/challenges";
import { fetchPathProgress } from "@/lib/paths";

export default function ProjectDetailPage({
  params,
}: {
  params: { projectId: string };
}) {
  const [project, setProject] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [progress, setProgress] = useState<any>(null);

  const [activeNode, setActiveNode] = useState<any>(null);
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [answer, setAnswer] = useState("");
  const [tutorResult, setTutorResult] = useState<TutorResult | null>(null);
  const [busy, setBusy] = useState(false);

useEffect(() => {
  Promise.all([
    fetchProject(params.projectId),
    fetchPathProgress(params.projectId),
  ])
    .then(([proj, prog]) => {
      setProject(proj);
      setProgress(prog);
    })
    .finally(() => setLoading(false));
}, [params.projectId]);

const progressMap = progress
  ? Object.fromEntries(
      progress.nodes.map((p: any) => [p.node_id, p])
    )
  : {};

  function getPrerequisites(nodeId: number): number[] {
    if (!project?.edges) return [];

    return project.edges
      .filter((e: any) => e.to_node_id === nodeId)
      .map((e: any) => e.from_node_id);
  }

  function isNodeLocked(nodeId: number): boolean {
    const prereqs = getPrerequisites(nodeId);

    // No prerequisites → not locked
    if (prereqs.length === 0) return false;

    // Locked if ANY prerequisite is not completed
    return prereqs.some(
      (pid) => progressMap[pid]?.status !== "completed"
    );
  }



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

    // 🔄 refresh progress
    const updatedProgress = await fetchPathProgress(params.projectId);
    setProgress(updatedProgress);

    setBusy(false);
  }


  if (loading) return <div className="p-6">Loading…</div>;
  if (!project) return <div className="p-6">Not found</div>;

  function StatusBadge({ status }: { status: string }) {
    const styles: Record<string, string> = {
      not_started: "bg-gray-200 text-gray-700",
      in_progress: "bg-blue-100 text-blue-700",
      completed: "bg-green-100 text-green-700",
      blocked: "bg-red-100 text-red-700",
    };

    return (
      <span
        className={`text-xs px-2 py-1 rounded ${
          styles[status] || "bg-gray-200"
        }`}
      >
        {status.replace("_", " ")}
      </span>
    );
  }

  function NodeTypeBadge({ type }: { type: string }) {
    const meta = NODE_TYPE_META[type];

    if (!meta) return null;

    return (
      <span
        className={`text-xs px-2 py-1 rounded flex items-center gap-1 ${meta.className}`}
        title={meta.label}
      >
        <span>{meta.icon}</span>
        <span>{meta.label}</span>
      </span>
    );
  }


  const NODE_TYPE_META: Record<
    string,
    { label: string; icon: string; className: string }
  > = {
    concept: {
      label: "Concept",
      icon: "📘",
      className: "bg-blue-100 text-blue-700",
    },
    skill: {
      label: "Skill",
      icon: "🛠",
      className: "bg-yellow-100 text-yellow-700",
    },
    project: {
      label: "Project",
      icon: "🧪",
      className: "bg-purple-100 text-purple-700",
    },
    meta: {
      label: "Meta",
      icon: "🧠",
      className: "bg-gray-200 text-gray-700",
    },
  };



  return (
    <div className="max-w-5xl mx-auto p-6">
      <h1 className="text-2xl font-semibold">{project.goal_title}</h1>
      <p className="text-gray-600 mt-2 mb-6">{project.summary}</p>

      {/* Nodes list */}
      <div className="space-y-4">
        {project.nodes.map((node: any, idx: number) => {
          const nodeProgress = progress?.nodes.find(
            (p: any) => p.node_id === node.id
          );
          const locked = isNodeLocked(node.id);
          const missingPrereqs = getPrerequisites(node.id).filter(
            (pid) => progressMap[pid]?.status !== "completed"
          );


          return (
            <div
              key={node.id}
              className="border rounded p-4 flex justify-between"
            >
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-medium">
                    {idx + 1}. {node.title}
                  </h3>
                  <NodeTypeBadge type={node.node_type} />
                  {nodeProgress && (
                    <StatusBadge status={nodeProgress.status} />
                  )}
                </div>

                <p className="text-sm text-gray-600 mt-1">
                  {node.description}
                </p>

                {nodeProgress?.last_score !== null && (
                  <p className="text-xs text-gray-500 mt-1">
                    Last score:{" "}
                    {Math.round((nodeProgress.last_score || 0) * 100)}%
                  </p>
                )}
              </div>


              <button
                onClick={() => startChallenge(node)}
                disabled={busy || locked}
                className={`text-sm px-3 py-1 rounded border ${
                  locked
                    ? "opacity-50 cursor-not-allowed"
                    : "hover:bg-gray-50"
                }`}
                title={
                  locked
                    ? `Complete ${missingPrereqs.length} prerequisite(s) first`
                    : "Take challenge"
                }
              >
                {locked ? "Locked" : "Take Challenge"}
              </button>
            </div>
          );
        })}

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

              {!tutorResult.pass_node && (
                <button
                  onClick={() => {
                    setTutorResult(null);
                    setAnswer("");
                  }}
                  className="mt-2 text-sm px-3 py-1 rounded border hover:bg-gray-50"
                >
                  Retry challenge
                </button>
              )}
            </div>
          )}

          {progress && (
            <div className="mb-6">
              <div className="flex justify-between text-sm mb-1">
                <span>Progress</span>
                <span>{Math.round(progress.completion_ratio * 100)}%</span>
              </div>
              <div className="w-full h-2 bg-gray-200 rounded">
                <div
                  className="h-2 bg-pink-600 rounded"
                  style={{
                    width: `${progress.completion_ratio * 100}%`,
                  }}
                />
              </div>
            </div>
          )}

        </div>
      )}
    </div>
  );
}
