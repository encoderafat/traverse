"use client";

import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";
import Link from "next/link";
import { fetchProjects, Project } from "@/lib/paths";
import { useRouter } from "next/navigation";

export default function ProjectsPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      if (!data.session) {
        router.push("/signin");
        return;
      }

      fetchProjects()
        .then(setProjects)
        .finally(() => setLoading(false));
    });
  }, []);

  if (loading) return <div className="p-6">Loading...</div>;
  if (error) return <div className="p-6 text-red-600">{error}</div>;

  return (
    <div className="max-w-5xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Your Learning Projects</h1>
        <Link
          href="/projects/new"
          className="px-4 py-2 rounded bg-pink-600 text-white hover:bg-pink-700"
        >
          New Project
        </Link>
      </div>

      {projects.length === 0 ? (
        <p className="text-gray-500">
          You haven’t created any learning paths yet.
        </p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {projects.map((p) => (
            <Link
              key={p.id}
              href={`/projects/${p.id}`}
              className="border rounded p-4 hover:shadow-sm transition"
            >
              <h2 className="font-medium text-lg">{p.goal_title}</h2>
              <p className="text-gray-600 text-sm mt-1">
                {p.summary || "No summary"}
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
