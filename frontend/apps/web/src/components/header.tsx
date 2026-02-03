"use client";

import Link from "next/link";
import { useState } from "react";

export default function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { href: "#how-it-works", label: "How it Works" },
    { href: "#diagnostics", label: "Diagnostics" },
    { href: "#models", label: "Models" },
  ] as const;

  return (
    <header className="w-full border-b border-black/5 dark:border-white/5 bg-[#f6f6f8]/80 dark:bg-[#101622]/80 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="size-8 flex items-center justify-center rounded bg-[#135bec]/10 text-[#135bec]">
            <span className="material-symbols-outlined">terminal</span>
          </div>
          <h1 className="text-sm font-bold tracking-widest uppercase font-mono">
            DIAGNOSTIC_SYS
          </h1>
        </div>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-8">
          {navLinks.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className="text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-[#135bec] dark:hover:text-[#135bec] transition-colors"
            >
              {label}
            </Link>
          ))}
        </nav>

        {/* Mobile Menu Button */}
        <div className="flex items-center gap-4">
          <button
            className="md:hidden text-slate-400 hover:text-white"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            <span className="material-symbols-outlined">
              {mobileMenuOpen ? "close" : "menu"}
            </span>
          </button>
        </div>
      </div>

      {/* Mobile Navigation */}
      {mobileMenuOpen && (
        <nav className="md:hidden border-t border-white/5 bg-[#101622] px-6 py-4">
          <div className="flex flex-col gap-4">
            {navLinks.map(({ href, label }) => (
              <Link
                key={href}
                href={href}
                className="text-sm font-medium text-slate-400 hover:text-[#135bec] transition-colors"
                onClick={() => setMobileMenuOpen(false)}
              >
                {label}
              </Link>
            ))}
          </div>
        </nav>
      )}
    </header>
  );
}
