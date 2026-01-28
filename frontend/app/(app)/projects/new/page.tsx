"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createPath } from "@/lib/paths";

export default function NewProjectPage() {
  const router = useRouter();

  const [goalTitle, setGoalTitle] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await createPath({
        goal_title: goalTitle,
        goal_description: description || undefined,
      });

      router.push("/projects");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-xl">
      <h1 className="text-2xl font-semibold mb-4">
        Create a learning project
      </h1>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">
            Goal
          </label>
          <input
            required
            value={goalTitle}
            onChange={(e) => setGoalTitle(e.target.value)}
            className="w-full border border-gray-300 rounded-md px-3 py-2"
            placeholder="e.g. Learn machine learning"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">
            Description (optional)
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full border border-gray-300 rounded-md px-3 py-2"
            rows={4}
          />
        </div>

        {error && (
          <p className="text-sm text-red-600">{error}</p>
        )}

        <button
          disabled={loading}
          className="rounded-md bg-black text-white px-4 py-2 text-sm hover:bg-gray-900 disabled:opacity-50"
        >
          {loading ? "Creating…" : "Create project"}
        </button>
      </form>
    </div>
  );
}
