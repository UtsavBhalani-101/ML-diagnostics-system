"use client";

import { Clock } from "lucide-react";

export default function HowItWorksPage() {
    return (
        <main className="flex-grow flex flex-col relative min-h-[calc(100vh-8rem)]">
            {/* Grid Pattern Background */}
            <div className="absolute inset-0 bg-grid-pattern pointer-events-none z-0" />

            <section className="relative z-10 flex flex-col items-center justify-center flex-grow py-32 px-6">
                <div className="max-w-2xl w-full text-center">
                    <div className="inline-flex items-center justify-center size-16 rounded-full bg-primary/10 text-primary mb-6">
                        <Clock className="size-8" />
                    </div>
                    <h1 className="text-4xl md:text-5xl font-bold tracking-tight mb-6 text-foreground">
                        How it Works
                    </h1>
                    <p className="text-lg text-muted-foreground font-mono mb-8">
                        This section is coming soon.
                    </p>
                    <div className="border border-border rounded-lg p-8 bg-card/50 backdrop-blur-sm">
                        <p className="text-muted-foreground font-mono text-sm">
                            We&apos;re building comprehensive documentation to explain the diagnostic pipeline,
                            analysis layers, and how the system evaluates your data before modeling.
                        </p>
                    </div>
                </div>
            </section>
        </main>
    );
}
