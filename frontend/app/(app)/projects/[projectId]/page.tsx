"use client";

import { useAuth } from "@/lib/useAuth";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function ProjectPage({ params }: { params: { projectId: string } }) {
  const { session, loading } = useAuth();
  const router = useRouter();

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
        Project {params.projectId}
      </h1>
    </div>
  );
}
