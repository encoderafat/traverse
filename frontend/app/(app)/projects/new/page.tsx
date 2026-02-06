"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createPath } from "@/lib/paths";
import { supabase } from "@/lib/supabase";

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
  const [progressMessage, setProgressMessage] = useState<string | null>(null);
  const [progressPercent, setProgressPercent] = useState<number>(0);

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
    setProgressMessage("Starting...");
    setProgressPercent(5);

    try {
      const backgroundParts = [
        currentSkills ? `Current skills: ${currentSkills}.` : null,
        learningStyle ? `Learning style: ${learningStyle}.` : null,
        timePerWeek ? `Time per week: ${timePerWeek}.` : null,
      ].filter(Boolean);
      const payload = {
        goal_title: `Learning Path for ${targetRole}`,
        goal_description: `${goalDescription} Goal: become a ${targetRole}.`,
        domain_hint: targetRole,
        level: experienceLevel,
        user_background: backgroundParts.join(" "),
      };

      const {
        data: { session },
      } = await supabase.auth.getSession();

      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (session?.access_token) {
        headers.Authorization = `Bearer ${session.access_token}`;
      }

      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/paths/stream`,
        {
          method: "POST",
          headers,
          body: JSON.stringify(payload),
        }
      );

      if (!res.ok || !res.body) {
        const text = await res.text();
        throw new Error(text || "Failed to create learning path.");
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const parts = buffer.split("\n\n");
        buffer = parts.pop() || "";

        for (const chunk of parts) {
          const lines = chunk.split("\n");
          const eventLine = lines.find((l) => l.startsWith("event:"));
          const dataLine = lines.find((l) => l.startsWith("data:"));
          const event = eventLine ? eventLine.replace("event:", "").trim() : "message";
          const dataText = dataLine ? dataLine.replace("data:", "").trim() : "{}";
          let data: any = {};
          try {
            data = JSON.parse(dataText);
          } catch {
            data = { message: dataText };
          }

          if (event === "progress") {
            if (typeof data.percent === "number") setProgressPercent(data.percent);
            if (data.message) setProgressMessage(data.message);
          } else if (event === "done") {
            setProgressPercent(100);
            setProgressMessage("Done.");
            router.push(`/projects/${data.path_id}`);
            return;
          } else if (event === "error") {
            setError(data.message || "Failed to create learning path.");
            setIsSubmitting(false);
            setProgressMessage(null);
            return;
          }
        }
      }
    } catch (err: any) {
      console.error("Failed to create path:", err);
      setError(err.message || "Failed to create learning path. Please try again.");
      setIsSubmitting(false);
      setProgressMessage(null);
    }
  };

  return (
    <div className="container mx-auto p-8 max-w-3xl">
      <div className="text-center mb-10">
        <p className="text-xs uppercase tracking-[0.2em] text-muted">New Path</p>
        <h1 className="text-4xl font-semibold heading-font text-primary mt-2">
        Start a New Learning Path
        </h1>
        <p className="text-sm text-muted mt-3">
          Answer a few questions and we will generate a tailored learning graph.
        </p>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
          <strong className="font-bold">Error!</strong>
          <span className="block sm:inline"> {error}</span>
        </div>
      )}

      {isSubmitting && progressMessage && (
        <div className="bg-surface border border-border text-slate-700 px-4 py-3 rounded-xl mb-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="font-semibold">{progressMessage}</span>
            <span className="text-sm">{progressPercent}%</span>
          </div>
          <div className="w-full h-2 bg-surface-alt rounded mt-2">
            <div
              className="h-2 rounded transition-all"
              style={{ width: `${progressPercent}%`, backgroundColor: "var(--accent)" }}
            />
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="card p-8">
        <div className="mb-6 flex items-center justify-between text-sm text-muted">
          <span>Step {step + 1} of {totalSteps + 1}</span>
          <div className="h-2 w-32 rounded-full bg-surface-alt">
            <div
              className="h-2 rounded-full"
              style={{
                width: `${((step + 1) / (totalSteps + 1)) * 100}%`,
                backgroundColor: "var(--accent)",
              }}
            />
          </div>
        </div>

        {step === 0 && (
          <div className="mb-6">
            <label htmlFor="targetRole" className="block text-slate-700 text-lg font-semibold mb-2">
              What do you want to become?
            </label>
            <input
              type="text"
              id="targetRole"
              className="input-field w-full"
              placeholder="e.g., Kubernetes DevOps Engineer"
              value={targetRole}
              onChange={(e) => setTargetRole(e.target.value)}
              required
              disabled={isSubmitting}
            />
            <p className="text-sm text-muted mt-2">
              Tell us your aspiration. Traverse will reverse-engineer the expertise required.
            </p>
          </div>
        )}

        {step === 1 && (
          <div className="mb-6">
            <label htmlFor="goalDescription" className="block text-slate-700 text-lg font-semibold mb-2">
              What’s your goal in your own words?
            </label>
            <textarea
              id="goalDescription"
              className="input-field w-full"
              placeholder="e.g., I want to deploy and monitor ML models reliably in production."
              value={goalDescription}
              onChange={(e) => setGoalDescription(e.target.value)}
              rows={4}
              required
              disabled={isSubmitting}
            />
            <p className="text-sm text-muted mt-2">
              This helps us tailor the research and challenges to your intent.
            </p>
          </div>
        )}

        {step === 2 && (
          <div className="mb-6">
            <label htmlFor="experienceLevel" className="block text-slate-700 text-lg font-semibold mb-2">
              What’s your current level?
            </label>
            <select
              id="experienceLevel"
              className="input-field w-full"
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
            <p className="text-sm text-muted mt-2">
              We’ll skip what you already know and focus on your gaps.
            </p>
          </div>
        )}

        {step === 3 && (
          <>
            <div className="mb-6">
              <label htmlFor="currentSkills" className="block text-slate-700 text-lg font-semibold mb-2">
                What do you already know? (Optional)
              </label>
              <input
                type="text"
                id="currentSkills"
                className="input-field w-full"
                placeholder="e.g., Python, Docker, Basic Networking (comma-separated)"
                value={currentSkills}
                onChange={(e) => setCurrentSkills(e.target.value)}
                disabled={isSubmitting}
              />
              <p className="text-sm text-muted mt-2">
                Help us personalize your path by listing skills you already possess.
              </p>
            </div>

            <div className="mb-6">
              <label htmlFor="learningStyle" className="block text-slate-700 text-lg font-semibold mb-2">
                How do you prefer to learn? (Optional)
              </label>
              <input
                type="text"
                id="learningStyle"
                className="input-field w-full"
                placeholder="e.g., hands-on projects, reading, videos, pair programming"
                value={learningStyle}
                onChange={(e) => setLearningStyle(e.target.value)}
                disabled={isSubmitting}
              />
            </div>

            <div className="mb-6">
              <label htmlFor="timePerWeek" className="block text-slate-700 text-lg font-semibold mb-2">
                How much time can you spend per week? (Optional)
              </label>
              <input
                type="text"
                id="timePerWeek"
                className="input-field w-full"
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
            <h2 className="text-2xl font-semibold heading-font text-primary mb-4">Review Your Interview</h2>
            <div className="space-y-4 bg-surface-alt border border-border rounded-xl p-4">
              <div>
                <p className="text-sm text-muted">Target Role</p>
                <p className="font-medium text-slate-900">{targetRole || "Not specified"}</p>
              </div>
              <div>
                <p className="text-sm text-muted">Goal Description</p>
                <p className="font-medium text-slate-900 whitespace-pre-wrap">{goalDescription || "Not specified"}</p>
              </div>
              <div>
                <p className="text-sm text-muted">Experience Level</p>
                <p className="font-medium text-slate-900">{experienceLevel || "Not specified"}</p>
              </div>
              <div>
                <p className="text-sm text-muted">Current Skills</p>
                <p className="font-medium text-slate-900">{currentSkills || "Not specified"}</p>
              </div>
              <div>
                <p className="text-sm text-muted">Learning Style</p>
                <p className="font-medium text-slate-900">{learningStyle || "Not specified"}</p>
              </div>
              <div>
                <p className="text-sm text-muted">Time Per Week</p>
                <p className="font-medium text-slate-900">{timePerWeek || "Not specified"}</p>
              </div>
            </div>
            <p className="text-sm text-muted mt-3">
              You can go back to edit any response before generating your path.
            </p>
          </div>
        )}

        <div className="flex gap-4">
          {step > 0 && (
            <button
              type="button"
              onClick={goBack}
              className="flex-1 btn-secondary"
              disabled={isSubmitting}
            >
              Back
            </button>
          )}

          {step < totalSteps && (
            <button
              type="button"
              onClick={goNext}
              className="flex-1 btn-primary"
              disabled={isSubmitting}
            >
              Continue
            </button>
          )}

          {step === totalSteps && (
            <button
              type="submit"
              className={`flex-1 btn-primary ${
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
