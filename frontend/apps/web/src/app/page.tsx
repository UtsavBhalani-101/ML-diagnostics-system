"use client";

import { useEffect, useState } from "react";
import { Hero } from "@/components/hero";
import { getHomePage, getHealth, HomePageResponse } from "@/lib/api";

export default function Home() {
  const [apiStatus, setApiStatus] = useState<"loading" | "connected" | "disconnected">("loading");
  const [apiInfo, setApiInfo] = useState<HomePageResponse | null>(null);

  useEffect(() => {
    async function checkBackend() {
      try {
        // Check health first
        await getHealth();

        // Then get home page info
        const homeData = await getHomePage();
        setApiInfo(homeData);
        setApiStatus("connected");
      } catch {
        setApiStatus("disconnected");
      }
    }

    checkBackend();
  }, []);

  return (
    <main className="flex-grow flex flex-col relative min-h-[calc(100vh-8rem)]">
      {/* Grid Pattern Background */}
      <div className="absolute inset-0 bg-grid-pattern pointer-events-none z-0" />

      {/* Center Vertical Line (Desktop) */}
      <div className="absolute top-0 bottom-0 left-1/2 w-px bg-gradient-to-b from-transparent via-border to-transparent hidden lg:block -translate-x-1/2 pointer-events-none z-0" />

      {/* Hero Section */}
      <section className="relative z-10 flex flex-col items-center justify-center flex-grow px-6">
        <Hero />

        {/* API Status Indicator */}
        <div className="mt-8 flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            {apiStatus === "loading" && (
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-yellow-500 opacity-75" />
            )}
            <span
              className={`relative inline-flex rounded-full h-2 w-2 ${apiStatus === "connected"
                  ? "bg-emerald-500"
                  : apiStatus === "disconnected"
                    ? "bg-red-500"
                    : "bg-yellow-500"
                }`}
            />
          </span>
          <span className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">
            Backend: {apiStatus === "connected" ? `Connected (v${apiInfo?.version || "?"})` : apiStatus}
          </span>
        </div>
      </section>

      {/* Bottom Divider */}
      <div className="absolute bottom-0 left-0 right-0 h-px bg-border z-0" />
    </main>
  );
}
