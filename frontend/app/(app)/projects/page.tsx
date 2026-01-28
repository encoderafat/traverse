"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { fetchPaths, LearningPath } from "@/lib/paths";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<LearningPath[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPaths()
      .then(setProjects)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <p className="text-gray-500">Loading projects…</p>;
  }

  if (error) {
    return <p className="text-red-600">{error}</p>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Learning Projects</h1>

        <Link
          href="/projects/new"
          className="rounded-md bg-black text-white px-4 py-2 text-sm hover:bg-gray-900"
        >
          New Project
        </Link>
      </div>

      {projects.length === 0 ? (
        <p className="text-gray-600">
          You haven’t created any learning projects yet.
        </p>
      ) : (
        <div className="grid gap-4">
          {projects.map((p) => (
            <Link
              key={p.id}
              href={`/projects/${p.id}`}
              className="block border border-gray-200 rounded-lg p-4 hover:border-gray-300"
            >
              <h2 className="font-medium">{p.goal_title}</h2>
              <p className="text-sm text-gray-600 mt-1">
                {p.summary || "No summary yet"}
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
