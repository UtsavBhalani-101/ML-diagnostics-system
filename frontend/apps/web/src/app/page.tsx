"use client";

import Link from "next/link";

export default function Home() {
  return (
    <main className="flex-grow flex flex-col relative">
      {/* Grid Pattern Background */}
      <div className="absolute inset-0 bg-grid-pattern pointer-events-none z-0" />

      {/* Hero Section */}
      <section className="relative z-10 flex flex-col items-center justify-center flex-grow py-32 px-6">
        {/* Center Vertical Line (Desktop) */}
        <div className="absolute top-0 bottom-0 left-1/2 w-px bg-gradient-to-b from-transparent via-white/10 to-transparent hidden lg:block -translate-x-1/2 pointer-events-none" />

        {/* Staging Module Container */}
        <div className="max-w-4xl w-full text-center relative staging-module py-16 px-8 border border-white/5 rounded-xl backdrop-blur-sm">
          {/* Status Indicator */}
          <div className="inline-flex items-center gap-3 px-4 py-1.5 rounded-full border border-[#135bec]/30 bg-[#135bec]/10 mb-10">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#135bec] opacity-75" />
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-[#135bec]" />
            </span>
            <span className="text-[10px] font-mono font-bold text-[#135bec] uppercase tracking-[0.2em]">
              Ready for Execution: System Operational
            </span>
          </div>

          {/* Main Headline */}
          <h2 className="text-5xl md:text-7xl font-bold tracking-tight mb-8 leading-[1.1] bg-clip-text text-transparent bg-gradient-to-b from-white to-white/60">
            Diagnostics First.
            <br />
            Modeling Second.
          </h2>

          {/* Supporting Text */}
          <p className="text-base md:text-lg text-slate-500 dark:text-slate-400 max-w-2xl mx-auto mb-12 font-mono leading-relaxed">
            Staging environment prepared. Ensure data readiness and mitigate
            model drift before deployment.
            <br className="hidden md:block" />
            Meticulous tools for high-stakes ML execution.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
            {/* Primary Button */}
            <Link
              href="/diagnostics"
              className="btn-shine group relative inline-flex h-14 items-center justify-center overflow-hidden rounded-md bg-[#135bec] px-10 font-bold text-white transition-all duration-300 hover:bg-[#135bec]/90 focus:outline-none focus:ring-2 focus:ring-[#135bec] focus:ring-offset-2 focus:ring-offset-[#101622] shadow-lg shadow-[#135bec]/20"
            >
              <span className="flex items-center gap-3">
                <span className="material-symbols-outlined text-[24px]">
                  play_circle
                </span>
                <span className="uppercase tracking-widest text-sm">
                  Initiate Diagnostics
                </span>
              </span>
            </Link>

            {/* Secondary Button */}
            <Link
              href="/docs"
              className="inline-flex h-14 items-center justify-center rounded-md border border-slate-700 bg-transparent px-10 font-medium text-slate-300 transition-colors hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2 focus:ring-offset-[#101622]"
            >
              <span className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[20px]">
                  menu_book
                </span>
                <span className="text-sm">View Documentation</span>
              </span>
            </Link>
          </div>

          {/* Bottom Status Bar */}
          <div className="mt-12 pt-8 border-t border-white/5 flex flex-col sm:flex-row justify-center gap-4 sm:gap-8 opacity-40">
            <div className="flex items-center justify-center gap-2">
              <span className="text-[10px] font-mono uppercase tracking-widest">
                Environment: Production
              </span>
            </div>
            <div className="flex items-center justify-center gap-2">
              <span className="text-[10px] font-mono uppercase tracking-widest">
                Thread State: Awaiting
              </span>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
