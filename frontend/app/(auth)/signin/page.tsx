"use client";

import { signInWithGithub } from "@/lib/auth";

export default function SignInPage() {
  const handleSignIn = async () => {
    const redirectTo = `${location.origin}/projects`;
    await signInWithGithub(redirectTo);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-white px-6">
      <div className="w-full max-w-sm border border-gray-200 rounded-lg p-6">
        <h1 className="text-xl font-semibold mb-2">
          Sign in to Traverse
        </h1>

        <p className="text-sm text-gray-600 mb-6">
          Continue to your learning projects
        </p>

        <button
          className="w-full rounded-md bg-black text-white py-2 text-sm hover:bg-gray-900"
          onClick={handleSignIn}
        >
          Sign in with GitHub
        </button>
      </div>
    </div>
  );
}
