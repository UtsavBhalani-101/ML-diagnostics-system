"use client";

import { useEffect, useState } from "react";
import { BookOpen, Layers3 } from "lucide-react";
import type { DocsResponse } from "@/lib/api";
import { getDocsContent } from "@/lib/api";

type PageState = "loading" | "ready" | "error";

export default function DocsPage() {
    const [pageState, setPageState] = useState<PageState>("loading");
    const [docs, setDocs] = useState<DocsResponse | null>(null);
    const [errorMessage, setErrorMessage] = useState("");

    useEffect(() => {
        async function loadDocs() {
            try {
                const response = await getDocsContent();
                setDocs(response);
                setPageState("ready");
            } catch (error) {
                setErrorMessage(error instanceof Error ? error.message : "Failed to load documentation.");
                setPageState("error");
            }
        }

        loadDocs();
    }, []);

    return (
        <main className="relative flex min-h-screen flex-grow flex-col">
            <div className="pointer-events-none absolute inset-0 z-0 bg-grid-pattern" />

            <section className="relative z-10 mx-auto flex w-full max-w-5xl flex-col gap-8 px-6 py-16">
                <div className="max-w-3xl">
                    <div className="mb-4 inline-flex size-14 items-center justify-center rounded-full bg-primary/10 text-primary">
                        <BookOpen className="size-7" />
                    </div>
                    <h1 className="text-4xl font-bold tracking-tight text-foreground md:text-5xl">
                        Documentation
                    </h1>
                    <p className="mt-4 font-mono text-sm text-muted-foreground md:text-base">
                        Real backend documentation for how to interpret the system before modeling.
                    </p>
                </div>

                {pageState === "loading" && (
                    <div className="rounded-xl border border-border bg-card/60 p-6 font-mono text-sm text-muted-foreground backdrop-blur">
                        Loading documentation...
                    </div>
                )}

                {pageState === "error" && (
                    <div className="rounded-xl border border-red-500/30 bg-red-500/5 p-6 font-mono text-sm text-red-400 backdrop-blur">
                        {errorMessage || "Documentation could not be loaded."}
                    </div>
                )}

                {pageState === "ready" && docs && (
                    <>
                        <section className="rounded-xl border border-border bg-card/60 p-6 backdrop-blur">
                            <h2 className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                                Overview
                            </h2>
                            <p className="mt-4 text-sm leading-7 text-foreground md:text-base">
                                {docs.overview}
                            </p>
                        </section>

                        <section className="rounded-xl border border-border bg-card/60 p-6 backdrop-blur">
                            <div className="flex items-center gap-3">
                                <div className="flex size-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                                    <Layers3 className="size-5" />
                                </div>
                                <div>
                                    <h2 className="text-lg font-semibold text-foreground">
                                        Layer 1: {docs.layers.layer_1.name}
                                    </h2>
                                    <p className="font-mono text-sm text-muted-foreground">
                                        {docs.layers.layer_1.purpose}
                                    </p>
                                </div>
                            </div>

                            <div className="mt-6 grid gap-4 md:grid-cols-3">
                                <DocCard
                                    title="Data Integrity"
                                    body={docs.layers.layer_1.dimensions.data_integrity}
                                />
                                <DocCard
                                    title="Target Validity"
                                    body={docs.layers.layer_1.dimensions.target_validity}
                                />
                                <DocCard
                                    title="Sample Adequacy"
                                    body={docs.layers.layer_1.dimensions.sample_adequacy}
                                />
                            </div>

                            <div className="mt-6 rounded-xl border border-white/8 bg-white/[0.03] p-5">
                                <h3 className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                                    Output Fields
                                </h3>
                                <div className="mt-4 grid gap-3 md:grid-cols-2">
                                    <DocField title="Risk Score (0-1)" body={docs.layers.layer_1.outputs.risk_score} />
                                    <DocField title="Status" body={docs.layers.layer_1.outputs.status} />
                                    <DocField title="Primary Causes" body={docs.layers.layer_1.outputs.primary_causes} />
                                    <DocField title="Contributing Factors" body={docs.layers.layer_1.outputs.contributing_factors} />
                                    <DocField title="Quick Actions" body={docs.layers.layer_1.outputs.quick_actions} />
                                </div>
                            </div>

                            <div className="mt-6 rounded-xl border border-amber-500/20 bg-amber-500/5 p-4 text-sm text-amber-100/90">
                                {docs.layers.layer_2.message}
                            </div>
                        </section>

                        <section className="rounded-xl border border-border bg-card/60 p-6 backdrop-blur">
                            <h2 className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                                How to Read Results
                            </h2>
                            <p className="mt-4 text-sm leading-7 text-foreground md:text-base">
                                {docs.interpretation}
                            </p>
                        </section>

                        <section className="rounded-xl border border-border bg-card/60 p-6 backdrop-blur">
                            <h2 className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                                Limitations
                            </h2>
                            <p className="mt-4 text-sm leading-7 text-foreground md:text-base">
                                {docs.limitations}
                            </p>
                        </section>
                    </>
                )}
            </section>
        </main>
    );
}

function DocCard({ title, body }: { title: string; body: string }) {
    return (
        <div className="rounded-xl border border-white/8 bg-white/[0.03] p-5">
            <h3 className="text-base font-semibold text-foreground">{title}</h3>
            <p className="mt-3 text-sm leading-6 text-muted-foreground">{body}</p>
        </div>
    );
}

function DocField({ title, body }: { title: string; body: string }) {
    return (
        <div className="rounded-lg border border-white/8 bg-black/10 p-4">
            <h4 className="text-sm font-semibold text-foreground">{title}</h4>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">{body}</p>
        </div>
    );
}
