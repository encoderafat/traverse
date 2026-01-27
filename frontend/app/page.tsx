// app/page.tsx
import Link from 'next/link';

export default function HomePage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center text-center">
      <h1 className="text-4xl font-bold mb-4">Welcome to Traverse</h1>
      <p className="text-lg text-gray-600 mb-8">
        Your AI-powered guide to mastering new skills.
      </p>
      <Link href="/projects" className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-3 px-6 rounded-lg text-lg">
        Get Started
      </Link>
    </div>
  );
}
