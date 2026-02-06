"use client";

import Link from "next/link";
import Image from "next/image";
import { useAuth } from "@/lib/useAuth";
import { signOut } from "@/lib/auth";

export default function Navbar() {
  const { session, loading } = useAuth();

  if (loading) return null;

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-surface backdrop-blur">
      <div className="mx-auto max-w-6xl px-6 py-5 flex items-center justify-between">
        <Link href="/projects" className="flex items-center gap-3 text-xl font-semibold heading-font text-primary">
          <Image src="/traverse.png" alt="Traverse logo" width={28} height={28} />
          <span>Traverse</span>
        </Link>

        {session && (
          <nav className="flex items-center gap-4 text-sm">
            <Link
              href="/projects"
              className="text-slate-600 hover:text-primary transition"
            >
              Projects
            </Link>

            <button
              onClick={signOut}
              className="btn-secondary text-sm"
            >
              Sign out
            </button>
          </nav>
        )}
      </div>
    </header>
  );
}
