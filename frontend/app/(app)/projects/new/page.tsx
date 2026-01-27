"use client";

import { useAuth } from "@/lib/useAuth";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function NewProjectPage() {
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
        New Project
      </h1>
    </div>
  );
}
