"use client";

import Link from "next/link";
import { useAuth } from "@/lib/useAuth";
import { signOut } from "@/lib/auth";

export default function Navbar() {
  const { session, loading } = useAuth();

  if (loading) return null;

  return (
    <header className="border-b border-gray-200">
      <div className="mx-auto max-w-6xl px-6 py-4 flex items-center justify-between">
        <Link href="/projects" className="text-lg font-semibold">
          Traverse
        </Link>

        {session && (
          <nav className="flex items-center gap-6 text-sm">
            <Link
              href="/projects"
              className="text-gray-700 hover:text-black"
            >
              Projects
            </Link>

            <button
              onClick={signOut}
              className="rounded-md border border-gray-300 px-3 py-1.5 hover:bg-gray-100"
            >
              Sign out
            </button>
          </nav>
        )}
      </div>
    </header>
  );
}
