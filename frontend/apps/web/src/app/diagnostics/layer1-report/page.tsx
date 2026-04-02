"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import type { Route } from "next";
import { Activity, Database, HardDrive, BarChart3 } from "lucide-react";
import type { Layer1FinalOutput, Layer1KeyFacts, DimensionResult } from "@/lib/api";
import { getLayer1Output } from "@/lib/api";
import { RiskGauge } from "@/components/diagnostics/risk-gauge";
import { RiskBar } from "@/components/diagnostics/risk-bar";
import { DimensionCard } from "@/components/diagnostics/dimension-card";

type PageState = "loading" | "empty" | "ready" | "error";

// ── Dimension display name mapping ──
const DIMENSION_ORDER: Array<{ key: string; label: string }> = [
    { key: "data_integrity", label: "Data Integrity" },
    { key: "target_viability", label: "Target Viability" },
    { key: "sample_adequacy", label: "Sample Adequacy" },
];

export default function Layer1ReportPage() {
    const [pageState, setPageState] = useState<PageState>("loading");
    const [data, setData] = useState<Layer1FinalOutput | null>(null);
    const [facts, setFacts] = useState<Layer1KeyFacts | null>(null);

    useEffect(() => {
        async function fetchData() {
            try {
                const response = await getLayer1Output();
                const output = response?.final_output;
                if (!output || !output.overall) {
                    setPageState("empty");
                    return;
                }
                setData(output);

                // Extract key facts from logic.facts
                const keyFacts = response?.logic?.facts;
                if (keyFacts) setFacts(keyFacts);

                setPageState("ready");
            } catch {
                setPageState("empty");
            }
        }
        fetchData();
    }, []);

    // Sort dimensions by risk severity (highest first)
    const sortedDimensions = useMemo(() => {
        if (!data?.dimensions) return [];
        return DIMENSION_ORDER
            .map(({ key }) => ({
                key,
                dimension: (data.dimensions as Record<string, DimensionResult>)[key],
            }))
            .filter((d) => d.dimension != null)
            .sort((a, b) => b.dimension.risk - a.dimension.risk);
    }, [data]);

    // ── Loading ──
    if (pageState === "loading") {
        return (
            <main className="flex-grow flex items-center justify-center min-h-[calc(100vh-8rem)]">
                <div className="absolute inset-0 bg-grid-pattern pointer-events-none z-0" />
                <div className="relative z-10 flex flex-col items-center gap-4">
                    <div className="size-12 rounded-full border-2 border-primary/30 border-t-primary animate-spin" />
                    <p className="text-muted-foreground font-mono text-sm tracking-wide">
                        Loading structural risk assessment…
                    </p>
                </div>
            </main>
        );
    }

    // ── Empty / Error ──
    if (pageState === "empty" || !data) {
        return (
            <main className="flex-grow flex items-center justify-center min-h-[calc(100vh-8rem)]">
                <div className="absolute inset-0 bg-grid-pattern pointer-events-none z-0" />
                <div className="relative z-10 flex flex-col items-center gap-6 text-center px-6">
                    <div className="size-16 rounded-full bg-white/5 border border-white/10 flex items-center justify-center">
                        <Activity className="size-8 text-muted-foreground" />
                    </div>
                    <div>
                        <h2 className="text-xl font-semibold mb-2">No diagnostics report available.</h2>
                        <p className="text-muted-foreground font-mono text-sm">
                            Please run Layer 1 analysis first.
                        </p>
                    </div>
                    <Link
                        href={"/diagnostics" as Route}
                        className="inline-flex items-center gap-2 px-6 py-2.5 rounded-lg bg-primary text-white text-sm font-medium hover:bg-primary/90 transition-colors"
                    >
                        ← Back to Diagnostics
                    </Link>
                </div>
            </main>
        );
    }

    return (
        <main className="flex-grow flex flex-col relative min-h-[calc(100vh-8rem)]">
            <div className="absolute inset-0 bg-grid-pattern pointer-events-none z-0" />

            <section className="relative z-10 w-full max-w-6xl mx-auto py-14 px-6 md:px-8 flex flex-col gap-10">
                {/* ── Breadcrumb ── */}
                <div className="flex items-center gap-3">
                    <Link
                        href={"/diagnostics" as Route}
                        className="text-muted-foreground hover:text-foreground transition-colors text-base font-mono"
                    >
                        ← Diagnostics
                    </Link>
                    <span className="text-muted-foreground/40">/</span>
                    <span className="text-base font-mono text-foreground">
                        Structural Risk Assessment
                    </span>
                </div>

                {/* ── Layer Context ── */}
                <div>
                    <p className="text-base font-semibold font-mono tracking-wide text-muted-foreground">
                        Layer 1 — Structural Risk Assessment
                    </p>
                    <p className="text-sm font-mono text-muted-foreground/75 mt-0.5">
                        Pre-model data quality evaluation across 3 structural dimensions.
                    </p>
                </div>

                {/* ══════════════════════════════════════════════
                    1. HERO SECTION — Overall Risk
                ══════════════════════════════════════════════ */}
                <div className="rounded-xl border border-white/[0.06] bg-card/60 backdrop-blur p-8 md:p-10 flex flex-col items-center">
                    <h2 className="text-xs font-mono font-semibold uppercase tracking-[0.2em] text-muted-foreground mb-6">
                        Overall Data Risk
                    </h2>

                    <RiskGauge
                        risk={data.overall.risk}
                        status={data.overall.status}
                    />

                    {/* Full-width risk bar */}
                    <div className="w-full max-w-lg mt-8">
                        <RiskBar
                            risk={data.overall.risk}
                            height="h-2.5"
                            showMarker={true}
                            showLabels={true}
                        />
                    </div>
                </div>

                {/* ══════════════════════════════════════════════
                    2. DATA OVERVIEW (Key Facts)
                ══════════════════════════════════════════════ */}
                {facts && (
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                        {/* Dataset Dimensions */}
                        <div className="rounded-xl border border-white/[0.06] bg-card/60 backdrop-blur p-5">
                            <div className="flex items-center gap-2 mb-4">
                                <Database className="size-4 text-primary" />
                                <h3 className="text-xs font-mono font-semibold uppercase tracking-widest text-muted-foreground">
                                    Dataset
                                </h3>
                            </div>
                            <div className="space-y-2.5 text-sm font-mono">
                                <FactRow label="Shape" value={facts.dimensions.shape} />
                                <FactRow label="Rows" value={facts.dimensions.rows.toLocaleString()} />
                                <FactRow label="Columns" value={String(facts.dimensions.columns)} />
                                <FactRow label="Scale" value={facts.dimensions.scale_class} />
                            </div>
                        </div>

                        {/* Memory */}
                        <div className="rounded-xl border border-white/[0.06] bg-card/60 backdrop-blur p-5">
                            <div className="flex items-center gap-2 mb-4">
                                <HardDrive className="size-4 text-primary" />
                                <h3 className="text-xs font-mono font-semibold uppercase tracking-widest text-muted-foreground">
                                    Memory
                                </h3>
                            </div>
                            <div className="space-y-2.5 text-sm font-mono">
                                <FactRow label="Usage" value={`${facts.memory.memory_mb} MB`} />
                                <FactRow label="Class" value={facts.memory.memory_class} />
                            </div>
                        </div>

                        {/* Feature Mix */}
                        <div className="rounded-xl border border-white/[0.06] bg-card/60 backdrop-blur p-5">
                            <div className="flex items-center gap-2 mb-4">
                                <BarChart3 className="size-4 text-primary" />
                                <h3 className="text-xs font-mono font-semibold uppercase tracking-widest text-muted-foreground">
                                    Feature Mix
                                </h3>
                            </div>
                            <div className="space-y-2.5 text-sm font-mono">
                                <FactRow label="Type" value={facts.feature_mix.mix_type} />
                                <FactRow label="Numeric" value={`${(facts.feature_mix.num_ratio * 100).toFixed(0)}%`} />
                                <FactRow label="Categorical" value={`${(facts.feature_mix.cat_ratio * 100).toFixed(0)}%`} />
                            </div>
                        </div>
                    </div>
                )}

                {/* ══════════════════════════════════════════════
                    3. DIMENSION CARDS
                ══════════════════════════════════════════════ */}
                <div>
                    <h2 className="text-xs font-mono font-semibold uppercase tracking-[0.2em] text-muted-foreground mb-5">
                        Structural Dimensions
                        <span className="text-muted-foreground/40 ml-2">
                            — sorted by risk severity
                        </span>
                    </h2>

                    <div className="space-y-4">
                        {sortedDimensions.map(({ key, dimension }, index) => (
                            <DimensionCard
                                key={key}
                                name={key}
                                dimension={dimension}
                                defaultExpanded={index === 0}
                            />
                        ))}
                    </div>
                </div>

                {/* Bottom spacer */}
                <div className="h-8" />
            </section>
        </main>
    );
}

/* ──────────────────── Sub-component ──────────────────── */

function FactRow({ label, value }: { label: string; value: string }) {
    return (
        <div className="flex justify-between items-center">
            <span className="text-muted-foreground">{label}</span>
            <span className="font-medium text-foreground">{value}</span>
        </div>
    );
}
