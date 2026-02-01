"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createPath } from "@/lib/paths"; // Assuming createPath is the correct function for this. If not, please correct.

enum WizardStep {
  Briefing = "briefing",
  Researching = "researching",
  Review = "review",
  Completed = "completed",
}

export default function NewProjectPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState<WizardStep>(WizardStep.Briefing);
  const [targetRole, setTargetRole] = useState("");
  const [currentSkills, setCurrentSkills] = useState("");
  const [researchSummary, setResearchSummary] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmitBriefing = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetRole.trim()) {
      setError("Please specify a target role.");
      return;
    }
    setError(null);
    setIsSubmitting(true);
    setCurrentStep(WizardStep.Researching);

    try {
      // Simulate API call for research agent
      // In a real scenario, this would call your backend's research agent endpoint
      // and potentially stream updates or return a research ID for polling.
      const simulatedResearch = [
        `[In Progress] Analyzing job postings for "${targetRole}"...`,
        `[In Progress] Scanning expert blogs and documentation related to "${targetRole}"...`,
        `[In Progress] Identifying core concepts and prerequisites for "${targetRole}"...`,
        `[Done] Compiling key findings for review...`,
      ];
      // Simulate real-time updates to research summary
      for (let i = 0; i < simulatedResearch.length; i++) {
        await new Promise((resolve) => setTimeout(resolve, 1500)); // Simulate delay per step
        setResearchSummary((prev) => [...prev, simulatedResearch[i]]);
      }

      // After simulated research, move to review step
      await new Promise((resolve) => setTimeout(resolve, 1000)); // Additional delay before review
      setCurrentStep(WizardStep.Review);
    } catch (err) {
      console.error("Failed to initiate research:", err);
      setError("Failed to initiate research. Please try again.");
      setCurrentStep(WizardStep.Briefing); // Go back to briefing on error
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleConfirmResearch = async () => {
    setIsSubmitting(true);
    setError(null);
    try {
      // Call backend to create the path based on confirmed research and inputs
      // Assuming createPath now accepts targetRole and currentSkills
      const newPath = await createPath({
        goal_title: `Learning Path for ${targetRole}`, // Default title
        goal_description: `Personalized path to become a ${targetRole}. Pre-existing skills: ${currentSkills}.`,
        domain_hint: targetRole, // Use target role as domain hint for now
        level: "dynamic", // The agent will determine the actual level
        user_background: currentSkills,
        // In a real scenario, confirmed research findings/ID would be sent here
      });
      router.push(`/projects/${newPath.id}`); // Navigate to the new project page
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

      {currentStep === WizardStep.Briefing && (
        <form onSubmit={handleSubmitBriefing} className="bg-white p-8 rounded-lg shadow-lg border border-border">
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
            {isSubmitting ? "Starting Research..." : "Start Research"}
          </button>
        </form>
      )}

      {currentStep === WizardStep.Researching && (
        <div className="bg-white p-8 rounded-lg shadow-lg text-center border border-border">
          <h2 className="text-2xl font-bold mb-4 text-gray-900">
            Traverse is Researching Your Path...
          </h2>
          <div className="flex justify-center mb-6">
            {/* Simple loading spinner */}
            <div className="loader ease-linear rounded-full border-4 border-t-4 border-gray-200 h-12 w-12 mb-4 animate-spin" style={{ borderColor: 'var(--border)', borderTopColor: 'var(--accent)' }}></div>
          </div>
          <div className="text-left bg-gray-50 p-4 rounded max-h-64 overflow-y-auto border border-border">
            {researchSummary.map((line, index) => (
              <p key={index} className="text-gray-700 text-sm mb-1">
                {line}
              </p>
            ))}
          </div>
          <p className="text-gray-600 mt-4">
            This might take a moment as our Expertise Research Agent delves deep into the knowledge landscape.
          </p>
        </div>
      )}

      {currentStep === WizardStep.Review && (
        <div className="bg-white p-8 rounded-lg shadow-lg border border-border">
          <h2 className="text-2xl font-bold mb-4 text-gray-900 text-center">
            Research Complete! Review Findings
          </h2>
          <p className="text-gray-700 mb-6 text-center">
            Our Expertise Research Agent has completed its initial analysis for "
            <span className="font-semibold">{targetRole}</span>".
            Please review the key findings below.
          </p>
          <div className="bg-gray-50 p-6 rounded-lg mb-6 border border-border">
            <h3 className="text-xl font-semibold mb-3 text-gray-800">Key Competency Areas Identified:</h3>
            <ul className="list-disc pl-5 text-gray-700">
              {/* These would typically come from the backend after research */}
              <li>Deep understanding of Container Orchestration (Kubernetes, Docker Swarm)</li>
              <li>Proficiency in Infrastructure as Code (Terraform, Ansible)</li>
              <li>CI/CD Pipeline implementation and management (Jenkins, GitLab CI, ArgoCD)</li>
              <li>Monitoring and Observability tools (Prometheus, Grafana, ELK Stack)</li>
              <li>Cloud Provider Specific Knowledge (AWS, GCP, Azure)</li>
              <li>Network Fundamentals and Security in Cloud Environments</li>
            </ul>
            <p className="text-sm text-gray-600 mt-4">
              (In a full implementation, you could allow users to edit/confirm these points.)
            </p>
          </div>

          <p className="text-gray-700 mb-6 text-center">
            Does this accurately reflect your learning goals and the scope you envision?
          </p>

          <div className="flex justify-between gap-4">
            <button
              onClick={() => {setCurrentStep(WizardStep.Briefing); setResearchSummary([]);}} // Allow going back to edit initial input
              className="w-1/2 bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-3 px-4 rounded focus:outline-none focus:shadow-outline transition duration-200 ease-in-out"
              disabled={isSubmitting}
            >
              Go Back & Edit
            </button>
            <button
              onClick={handleConfirmResearch}
              className={`w-1/2 bg-accent hover:bg-pink-700 text-white font-bold py-3 px-4 rounded focus:outline-none focus:shadow-outline transition duration-200 ease-in-out ${
                isSubmitting ? "opacity-50 cursor-not-allowed" : ""
              }`}
              disabled={isSubmitting}
            >
              {isSubmitting ? "Building Path..." : "Confirm & Build Path"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
