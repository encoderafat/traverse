"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createPath } from "@/lib/paths";

export default function NewProjectPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [targetRole, setTargetRole] = useState("");
  const [goalDescription, setGoalDescription] = useState("");
  const [currentSkills, setCurrentSkills] = useState("");
  const [learningStyle, setLearningStyle] = useState("");
  const [timePerWeek, setTimePerWeek] = useState("");
  const [experienceLevel, setExperienceLevel] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const totalSteps = 4;

  const canProceedStep0 = targetRole.trim().length > 0;
  const canProceedStep1 = goalDescription.trim().length > 0;
  const canProceedStep2 = experienceLevel.trim().length > 0;
  const canProceedStep3 = true;

  const goNext = () => {
    setError(null);
    if (step === 0 && !canProceedStep0) {
      setError("Please specify a target role.");
      return;
    }
    if (step === 1 && !canProceedStep1) {
      setError("Please describe your goal.");
      return;
    }
    if (step === 2 && !canProceedStep2) {
      setError("Please select your current level.");
      return;
    }
    if (step === 3 && !canProceedStep3) {
      setError("Please review your responses.");
      return;
    }
    setStep(Math.min(step + 1, totalSteps));
  };

  const goBack = () => {
    setError(null);
    setStep(Math.max(step - 1, 0));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canProceedStep0 || !canProceedStep1 || !canProceedStep2) {
      setError("Please complete all required fields.");
      return;
    }
    setError(null);
    setIsSubmitting(true);

    try {
      const backgroundParts = [
        currentSkills ? `Current skills: ${currentSkills}.` : null,
        learningStyle ? `Learning style: ${learningStyle}.` : null,
        timePerWeek ? `Time per week: ${timePerWeek}.` : null,
      ].filter(Boolean);

      const newPath = await createPath({
        goal_title: `Learning Path for ${targetRole}`,
        goal_description: `${goalDescription} Goal: become a ${targetRole}.`,
        domain_hint: targetRole,
        level: experienceLevel,
        user_background: backgroundParts.join(" "),
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
        <div className="mb-6 text-sm text-gray-500">
          Step {step + 1} of {totalSteps + 1}
        </div>

        {step === 0 && (
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
        )}

        {step === 1 && (
          <div className="mb-6">
            <label htmlFor="goalDescription" className="block text-gray-700 text-lg font-semibold mb-2">
              What’s your goal in your own words?
            </label>
            <textarea
              id="goalDescription"
              className="shadow appearance-none border rounded w-full py-3 px-4 text-gray-700 leading-tight focus:outline-none focus:shadow-outline focus:border-accent"
              placeholder="e.g., I want to deploy and monitor ML models reliably in production."
              value={goalDescription}
              onChange={(e) => setGoalDescription(e.target.value)}
              rows={4}
              required
              disabled={isSubmitting}
            />
            <p className="text-sm text-gray-500 mt-2">
              This helps us tailor the research and challenges to your intent.
            </p>
          </div>
        )}

        {step === 2 && (
          <div className="mb-6">
            <label htmlFor="experienceLevel" className="block text-gray-700 text-lg font-semibold mb-2">
              What’s your current level?
            </label>
            <select
              id="experienceLevel"
              className="shadow appearance-none border rounded w-full py-3 px-4 text-gray-700 leading-tight focus:outline-none focus:shadow-outline focus:border-accent"
              value={experienceLevel}
              onChange={(e) => setExperienceLevel(e.target.value)}
              required
              disabled={isSubmitting}
            >
              <option value="" disabled>Select one</option>
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </select>
            <p className="text-sm text-gray-500 mt-2">
              We’ll skip what you already know and focus on your gaps.
            </p>
          </div>
        )}

        {step === 3 && (
          <>
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

            <div className="mb-6">
              <label htmlFor="learningStyle" className="block text-gray-700 text-lg font-semibold mb-2">
                How do you prefer to learn? (Optional)
              </label>
              <input
                type="text"
                id="learningStyle"
                className="shadow appearance-none border rounded w-full py-3 px-4 text-gray-700 leading-tight focus:outline-none focus:shadow-outline focus:border-accent"
                placeholder="e.g., hands-on projects, reading, videos, pair programming"
                value={learningStyle}
                onChange={(e) => setLearningStyle(e.target.value)}
                disabled={isSubmitting}
              />
            </div>

            <div className="mb-6">
              <label htmlFor="timePerWeek" className="block text-gray-700 text-lg font-semibold mb-2">
                How much time can you spend per week? (Optional)
              </label>
              <input
                type="text"
                id="timePerWeek"
                className="shadow appearance-none border rounded w-full py-3 px-4 text-gray-700 leading-tight focus:outline-none focus:shadow-outline focus:border-accent"
                placeholder="e.g., 4-6 hours/week"
                value={timePerWeek}
                onChange={(e) => setTimePerWeek(e.target.value)}
                disabled={isSubmitting}
              />
            </div>
          </>
        )}

        {step === 4 && (
          <div className="mb-6">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">Review Your Interview</h2>
            <div className="space-y-4 bg-gray-50 border rounded p-4">
              <div>
                <p className="text-sm text-gray-500">Target Role</p>
                <p className="font-medium text-gray-900">{targetRole || "Not specified"}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Goal Description</p>
                <p className="font-medium text-gray-900 whitespace-pre-wrap">{goalDescription || "Not specified"}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Experience Level</p>
                <p className="font-medium text-gray-900">{experienceLevel || "Not specified"}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Current Skills</p>
                <p className="font-medium text-gray-900">{currentSkills || "Not specified"}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Learning Style</p>
                <p className="font-medium text-gray-900">{learningStyle || "Not specified"}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Time Per Week</p>
                <p className="font-medium text-gray-900">{timePerWeek || "Not specified"}</p>
              </div>
            </div>
            <p className="text-sm text-gray-500 mt-3">
              You can go back to edit any response before generating your path.
            </p>
          </div>
        )}

        <div className="flex gap-4">
          {step > 0 && (
            <button
              type="button"
              onClick={goBack}
              className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-3 px-4 rounded focus:outline-none focus:shadow-outline transition duration-200 ease-in-out"
              disabled={isSubmitting}
            >
              Back
            </button>
          )}

          {step < totalSteps && (
            <button
              type="button"
              onClick={goNext}
              className="flex-1 bg-accent hover:bg-pink-700 text-white font-bold py-3 px-4 rounded focus:outline-none focus:shadow-outline transition duration-200 ease-in-out"
              disabled={isSubmitting}
            >
              Continue
            </button>
          )}

          {step === totalSteps && (
            <button
              type="submit"
              className={`flex-1 bg-accent hover:bg-pink-700 text-white font-bold py-3 px-4 rounded focus:outline-none focus:shadow-outline transition duration-200 ease-in-out ${
                isSubmitting ? "opacity-50 cursor-not-allowed" : ""
              }`}
              disabled={isSubmitting}
            >
              {isSubmitting ? "Building Path..." : "Build My Learning Path"}
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
