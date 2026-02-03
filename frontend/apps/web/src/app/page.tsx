"use client";

import { Hero } from "@/components/hero";

export default function Home() {
  return (
    <main className="flex-grow flex flex-col relative min-h-[calc(100vh-8rem)]">
      {/* Grid Pattern Background */}
      <div className="absolute inset-0 bg-grid-pattern pointer-events-none z-0" />

      {/* Center Vertical Line (Desktop) */}
      <div className="absolute top-0 bottom-0 left-1/2 w-px bg-gradient-to-b from-transparent via-border to-transparent hidden lg:block -translate-x-1/2 pointer-events-none z-0" />

      {/* Hero Section */}
      <section className="relative z-10 flex flex-col items-center justify-center flex-grow px-6">
        <Hero />
      </section>

      {/* Bottom Divider */}
      <div className="absolute bottom-0 left-0 right-0 h-px bg-border z-0" />
    </main>
  );
}
