"use client";

import { useEffect, useState } from "react";
import { Layers } from "lucide-react";
import type { ModelsResponse } from "@/lib/api";
import { getModelsContent } from "@/lib/api";

type PageState = "loading" | "ready" | "error";

export default function ModelsPage() {
    const [pageState, setPageState] = useState<PageState>("loading");
    const [models, setModels] = useState<ModelsResponse | null>(null);
    const [errorMessage, setErrorMessage] = useState("");

    useEffect(() => {
        async function loadModels() {
            try {
                const response = await getModelsContent();
                setModels(response);
                setPageState("ready");
            } catch (error) {
                setErrorMessage(error instanceof Error ? error.message : "Failed to load model status.");
                setPageState("error");
            }
        }

        loadModels();
    }, []);

    return (
        <main className="relative flex min-h-[calc(100vh-8rem)] flex-grow flex-col">
            <div className="pointer-events-none absolute inset-0 z-0 bg-grid-pattern" />

            <section className="relative z-10 flex flex-grow flex-col items-center justify-center px-6 py-20">
                <div className="w-full max-w-2xl text-center">
                    <div className="mb-6 inline-flex size-16 items-center justify-center rounded-full bg-primary/10 text-primary">
                        <Layers className="size-8" />
                    </div>
                    <h1 className="text-4xl font-bold tracking-tight text-foreground md:text-5xl">
                        Models
                    </h1>
                    <p className="mx-auto mt-4 max-w-xl font-mono text-sm text-muted-foreground md:text-base">
                        This system evaluates data before modeling. It does not train or serve models yet.
                    </p>

                    {pageState === "loading" && (
                        <div className="mt-8 rounded-lg border border-border bg-card/50 p-6 font-mono text-sm text-muted-foreground backdrop-blur-sm">
                            Loading model layer status...
                        </div>
                    )}

                    {pageState === "error" && (
                        <div className="mt-8 rounded-lg border border-red-500/30 bg-red-500/5 p-6 font-mono text-sm text-red-400 backdrop-blur-sm">
                            {errorMessage || "Model layer status could not be loaded."}
                        </div>
                    )}

                    {pageState === "ready" && models && (
                        <div className="mt-8 rounded-lg border border-border bg-card/50 p-8 backdrop-blur-sm">
                            <p className="text-lg font-semibold text-foreground">
                                No models configured yet
                            </p>
                            <p className="mt-3 font-mono text-sm text-muted-foreground">
                                {models.message}
                            </p>
                            <div className="mt-6 space-y-3 text-left">
                                {models.roadmap.map((item) => (
                                    <div key={item} className="rounded-lg border border-white/8 bg-white/[0.03] px-4 py-3 text-sm text-foreground">
                                        {item}
                                    </div>
                                ))}
                                <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 px-4 py-3 text-sm text-amber-100/90">
                                    Layer 2 is currently being built. It is coming soon.
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </section>
        </main>
    );
}
