"use client";

import Link from "next/link";
import type { Route } from "next";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { AnimatedTabs } from "./animated-tabs";
import { AnimatedThemeToggler } from "./ui/animated-theme-toggler";

export default function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const pathname = usePathname();

  const navTabs = [
    { label: "How it Works", href: "/how-it-works" },
    { label: "Diagnostics", href: "/diagnostics" },
    { label: "Models", href: "/models" },
    { label: "Docs", href: "/docs" },
  ];

  const isActivePath = (href: string) =>
    pathname === href || pathname.startsWith(`${href}/`);

  return (
    <header className="sticky top-0 z-50 w-full border-b border-black/5 bg-[#f6f6f8]/80 backdrop-blur-md dark:border-white/10 dark:bg-black/80">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        <Link href="/" className="flex items-center gap-3">
          <div className="flex size-8 items-center justify-center rounded bg-primary/10 text-primary">
            <span className="material-symbols-outlined">terminal</span>
          </div>
          <h1 className="font-mono text-sm font-bold uppercase tracking-widest">
            DIAGNOSTIC_SYS
          </h1>
        </Link>

        <nav className="hidden items-center gap-6 md:flex">
          <AnimatedTabs tabs={navTabs} />
          <AnimatedThemeToggler className="flex size-8 cursor-pointer items-center justify-center rounded-full border border-primary/10 bg-secondary/50 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground" />
        </nav>

        <div className="flex items-center gap-3 md:hidden">
          <AnimatedThemeToggler className="flex size-8 cursor-pointer items-center justify-center rounded-full border border-primary/10 bg-secondary/50 text-muted-foreground transition-colors hover:text-foreground [&_svg]:size-4" />
          <button
            className="text-slate-400 transition-colors hover:text-white"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            <span className="material-symbols-outlined">
              {mobileMenuOpen ? "close" : "menu"}
            </span>
          </button>
        </div>
      </div>

      {mobileMenuOpen && (
        <nav className="border-t border-white/10 bg-black px-6 py-4 md:hidden">
          <div className="flex flex-col gap-4">
            {navTabs.map(({ href, label }) => (
              <Link
                key={href}
                href={href as Route}
                className={`text-sm font-medium transition-colors ${
                  isActivePath(href)
                    ? "text-primary"
                    : "text-slate-400 hover:text-primary"
                }`}
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
