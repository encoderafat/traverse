// app/layout.tsx
import "./globals.css";

export const metadata = {
  title: "Traverse",
  description: "AI-powered learning paths",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-surface-alt text-slate-900 antialiased">
        {children}
      </body>
    </html>
  );
}
