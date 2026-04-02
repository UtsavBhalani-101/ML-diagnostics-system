"use client";

import Link from "next/link";
import { Clock } from "lucide-react";

export default function HowItWorksPage() {
    return (
        <main className="relative flex min-h-[calc(100vh-8rem)] flex-grow flex-col">
            <div className="pointer-events-none absolute inset-0 z-0 bg-grid-pattern" />

            <section className="relative z-10 mx-auto flex w-full max-w-4xl flex-col gap-6 px-6 py-16">
                <div className="max-w-2xl">
                    <div className="mb-6 inline-flex size-16 items-center justify-center rounded-full bg-primary/10 text-primary">
                        <Clock className="size-8" />
                    </div>
                    <h1 className="text-4xl font-bold tracking-tight text-foreground md:text-5xl">
                        How it Works
                    </h1>
                    <p className="mt-4 font-mono text-sm text-muted-foreground md:text-base">
                        The system is intentionally simple: validate first, interpret risk second, model later.
                    </p>
                </div>

                <div className="grid gap-4 md:grid-cols-3">
                    <StepCard
                        title="1. Upload"
                        body="A dataset is validated on the backend. Empty or invalid files are rejected immediately."
                    />
                    <StepCard
                        title="2. Diagnose"
                        body="Layer 1 extracts structural signals, converts them into risk by dimension, and returns a real report."
                    />
                    <StepCard
                        title="3. Decide"
                        body="Use the overall risk, dimension breakdown, primary causes, and quick actions to decide whether to proceed."
                    />
                </div>

                <div className="rounded-xl border border-border bg-card/60 p-6 backdrop-blur">
                    <h2 className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                        Current Scope
                    </h2>
                    <p className="mt-4 text-sm leading-7 text-foreground md:text-base">
                        Today the system ships a functional Layer 1 structural-risk slice across frontend and backend.
                        Layer 2 is currently being built and is coming soon. The models layer is not implemented yet,
                        so the product stays honest about what it can and cannot do right now.
                    </p>
                    <Link
                        href="/docs"
                        className="mt-5 inline-flex text-sm font-medium text-primary transition-colors hover:text-primary/80"
                    >
                        Read the full documentation
                    </Link>
                </div>
            </section>
        </main>
    );
}

function StepCard({ title, body }: { title: string; body: string }) {
    return (
        <div className="rounded-xl border border-border bg-card/60 p-5 backdrop-blur">
            <h2 className="text-base font-semibold text-foreground">{title}</h2>
            <p className="mt-3 text-sm leading-6 text-muted-foreground">{body}</p>
        </div>
    );
}
