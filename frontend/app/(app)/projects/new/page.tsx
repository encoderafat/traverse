"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createPath } from "@/lib/paths";

export default function NewProjectPage() {
  const router = useRouter();
  const [targetRole, setTargetRole] = useState("");
  const [currentSkills, setCurrentSkills] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetRole.trim()) {
      setError("Please specify a target role.");
      return;
    }
    setError(null);
    setIsSubmitting(true);

    try {
      const newPath = await createPath({
        goal_title: `Learning Path for ${targetRole}`,
        goal_description: `Personalized path to become a ${targetRole}. Pre-existing skills: ${currentSkills}.`,
        domain_hint: targetRole,
        level: "dynamic",
        user_background: currentSkills,
      });
      router.push(`/projects/${newPath.id}`);
    } catch (err: any) {
      console.error("Failed to create path:", err);
      setError(err.message || "Failed to create learning path. Please try again.");
      setIsSubmitting(false);
    }
  };

  return (
    <div className="container mx-auto p-8 max-w-3xl">
      <h1 className="text-4xl font-bold text-center mb-8 text-gray-900">
        Start a New Learning Path
      </h1>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
          <strong className="font-bold">Error!</strong>
          <span className="block sm:inline"> {error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white p-8 rounded-lg shadow-lg border border-border">
        <div className="mb-6">
          <label htmlFor="targetRole" className="block text-gray-700 text-lg font-semibold mb-2">
            What do you want to become?
          </label>
          <input
            type="text"
            id="targetRole"
            className="shadow appearance-none border rounded w-full py-3 px-4 text-gray-700 leading-tight focus:outline-none focus:shadow-outline focus:border-accent"
            placeholder="e.g., Kubernetes DevOps Engineer"
            value={targetRole}
            onChange={(e) => setTargetRole(e.target.value)}
            required
            disabled={isSubmitting}
          />
          <p className="text-sm text-gray-500 mt-2">
            Tell us your aspiration. Traverse will reverse-engineer the expertise required.
          </p>
        </div>

        <div className="mb-6">
          <label htmlFor="currentSkills" className="block text-gray-700 text-lg font-semibold mb-2">
            What do you already know? (Optional)
          </label>
          <input
            type="text"
            id="currentSkills"
            className="shadow appearance-none border rounded w-full py-3 px-4 text-gray-700 leading-tight focus:outline-none focus:shadow-outline focus:border-accent"
            placeholder="e.g., Python, Docker, Basic Networking (comma-separated)"
            value={currentSkills}
            onChange={(e) => setCurrentSkills(e.target.value)}
            disabled={isSubmitting}
          />
          <p className="text-sm text-gray-500 mt-2">
            Help us personalize your path by listing skills you already possess.
          </p>
        </div>

        <button
          type="submit"
          className={`w-full bg-accent hover:bg-pink-700 text-white font-bold py-3 px-4 rounded focus:outline-none focus:shadow-outline transition duration-200 ease-in-out ${
            isSubmitting ? "opacity-50 cursor-not-allowed" : ""
          }`}
          disabled={isSubmitting}
        >
          {isSubmitting ? "Building Path..." : "Build My Learning Path"}
        </button>
      </form>
    </div>
  );
}