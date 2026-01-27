"use client";

import { useAuth } from "@/lib/useAuth";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

// app/(app)/projects/page.tsx
export default function ProjectsPage() {
  const { session, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (window.location.hash.includes("access_token")) {
      router.replace("/projects");
    }
  }, [router]);

  useEffect(() => {
    if (!loading && !session) {
      router.push("/signin");
    }
  }, [loading, session, router]);

  if (loading || !session) {
    return null;
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-4">
        Learning Projects
      </h1>

      <p className="text-gray-600">
        Your learning paths will appear here.
      </p>
    </div>
  );
}
