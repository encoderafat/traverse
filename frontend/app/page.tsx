// app/page.tsx
import Link from 'next/link';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-surface-alt">
      <div className="mx-auto max-w-6xl px-6 py-20 grid grid-cols-1 lg:grid-cols-[1.1fr_0.9fr] gap-12 items-center">
        <div>
          <p className="text-sm uppercase tracking-[0.2em] text-muted mb-4">
            Personalized learning paths
          </p>
          <h1 className="text-5xl md:text-6xl font-semibold heading-font text-primary mb-6">
            Build expertise faster with adaptive, real-world learning paths.
          </h1>
          <p className="text-lg text-slate-600 mb-8 max-w-xl">
            Traverse analyzes real job signals and expert knowledge to design a learning graph
            tailored to what you already know, plus challenges that prove real competency.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link href="/projects" className="btn-primary text-base">
              Get Started
            </Link>
            <Link href="/signin" className="btn-secondary text-base">
              Sign in
            </Link>
          </div>
        </div>
        <div className="card p-8 bg-surface">
          <h2 className="text-xl font-semibold heading-font text-primary mb-3">
            What you get
          </h2>
          <ul className="space-y-3 text-slate-600 text-sm">
            <li>Research-backed competencies mapped into a clear DAG.</li>
            <li>Challenges that mirror real professional scenarios.</li>
            <li>Adaptive remediation when you get stuck.</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
