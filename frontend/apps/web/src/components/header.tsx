"use client";

import Link from "next/link";
import { useState } from "react";
import { AnimatedTabs } from "./animated-tabs";
import { AnimatedThemeToggler } from "./ui/animated-theme-toggler";

export default function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navTabs = [
    { label: "How it Works", href: "/how-it-works" },
    { label: "Diagnostics", href: "/diagnostics" },
    { label: "Models", href: "/models" },
  ];

  return (
    <header className="w-full border-b border-black/5 dark:border-white/10 bg-[#f6f6f8]/80 dark:bg-black/80 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-3">
          <div className="size-8 flex items-center justify-center rounded bg-primary/10 text-primary">
            <span className="material-symbols-outlined">terminal</span>
          </div>
          <h1 className="text-sm font-bold tracking-widest uppercase font-mono">
            DIAGNOSTIC_SYS
          </h1>
        </Link>

        {/* Desktop Navigation - Animated Tabs */}
        <nav className="hidden md:flex items-center gap-6">
          <AnimatedTabs tabs={navTabs} />

          {/* Theme Toggler */}
          <AnimatedThemeToggler
            className="size-8 flex items-center justify-center rounded-full bg-secondary/50 border border-primary/10 text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors cursor-pointer"
          />
        </nav>

        {/* Mobile Menu Button & Theme Toggle */}
        <div className="flex items-center gap-3 md:hidden">
          <AnimatedThemeToggler
            className="size-8 flex items-center justify-center rounded-full bg-secondary/50 border border-primary/10 text-muted-foreground hover:text-foreground transition-colors cursor-pointer [&_svg]:size-4"
          />
          <button
            className="text-slate-400 hover:text-white"
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
        <nav className="md:hidden border-t border-white/10 bg-black px-6 py-4">
          <div className="flex flex-col gap-4">
            {navTabs.map(({ href, label }) => (
              <Link
                key={href}
                href={href}
                className="text-sm font-medium text-slate-400 hover:text-primary transition-colors"
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
