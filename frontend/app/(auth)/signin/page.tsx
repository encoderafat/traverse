"use client";

import { signInWithGithub, signInWithGoogle } from "@/lib/auth";

export default function SignInPage() {
  const handleSignIn = async () => {
    const redirectTo = `${location.origin}/projects`;
    await signInWithGithub(redirectTo);
  };

  const handleGoogleSignIn = async () => {
    const redirectTo = `${location.origin}/projects`;
    await signInWithGoogle(redirectTo);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-alt px-6">
      <div className="w-full max-w-sm card p-8">
        <h1 className="text-2xl font-semibold heading-font text-primary mb-2">
          Sign in to Traverse
        </h1>

        <p className="text-sm text-muted mb-6">
          Continue to your learning projects
        </p>

        <button
          className="w-full btn-primary text-sm"
          onClick={handleSignIn}
        >
          Sign in with GitHub
        </button>

        <button
          className="w-full mt-3 btn-secondary text-sm"
          onClick={handleGoogleSignIn}
        >
          Sign in with Google
        </button>
      </div>
    </div>
  );
}
