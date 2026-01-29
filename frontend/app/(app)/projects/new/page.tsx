"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createProject } from "@/lib/paths";

export default function NewProjectPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const form = e.currentTarget;
    const data = new FormData(form);

    try {
      const res = await createProject({
        goal_title: data.get("goal_title") as string,
        goal_description: data.get("goal_description") as string,
        domain_hint: data.get("domain_hint") as string,
        level: data.get("level") as string,
        user_background: data.get("user_background") as string,
      });

      router.push(`/projects/${res.id}`);
    } catch (err: any) {
      setError(err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-3xl mx-auto p-6">
      <h1 className="text-2xl font-semibold mb-6">
        Create a Learning Project
      </h1>

      <form onSubmit={onSubmit} className="space-y-4">
        <input
          name="goal_title"
          required
          placeholder="Goal (e.g. Learn Machine Learning)"
          className="w-full border rounded px-3 py-2"
        />

        <textarea
          name="goal_description"
          placeholder="What do you want to achieve?"
          className="w-full border rounded px-3 py-2"
        />

        <input
          name="domain_hint"
          placeholder="Domain (e.g. software, music, fitness)"
          className="w-full border rounded px-3 py-2"
        />

        <select
          name="level"
          className="w-full border rounded px-3 py-2"
        >
          <option value="">Level</option>
          <option value="beginner">Beginner</option>
          <option value="intermediate">Intermediate</option>
          <option value="advanced">Advanced</option>
        </select>

        <textarea
          name="user_background"
          placeholder="Your background / constraints"
          className="w-full border rounded px-3 py-2"
        />

        {error && <p className="text-red-600">{error}</p>}

        <button
          disabled={loading}
          className="bg-pink-600 text-white px-4 py-2 rounded hover:bg-pink-700"
        >
          {loading ? "Creating…" : "Create Project"}
        </button>
      </form>
    </div>
  );
}
