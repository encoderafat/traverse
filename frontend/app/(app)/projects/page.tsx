"use client";

import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";
import Link from "next/link";
import { fetchPaths, LearningPath } from "@/lib/paths";
import { useRouter } from "next/navigation";

export default function ProjectsPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<LearningPath[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      if (!data.session) {
        router.push("/signin");
        return;
      }

      fetchPaths()
        .then(setProjects)
        .finally(() => setLoading(false));
    });
  }, []);

  if (loading) return <div className="p-6">Loading...</div>;
  if (error) return <div className="p-6 text-red-600">{error}</div>;

  return (
    <div className="max-w-5xl mx-auto p-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-muted">Dashboard</p>
          <h1 className="text-3xl font-semibold heading-font text-primary">Your Learning Projects</h1>
        </div>
        <Link
          href="/projects/new"
          className="btn-primary text-sm"
        >
          New Project
        </Link>
      </div>

      {projects.length === 0 ? (
        <p className="text-muted">
          You haven’t created any learning paths yet.
        </p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {projects.map((p) => (
            <Link
              key={p.id}
              href={`/projects/${p.id}`}
              className="card p-5 hover:shadow-xl transition"
            >
              <h2 className="font-semibold text-lg text-slate-900">{p.goal_title}</h2>
              <p className="text-muted text-sm mt-2">
                {p.summary || "No summary"}
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
