"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type { Route } from "next";
import { Activity, Database, HardDrive, BarChart3 } from "lucide-react";
import type { Layer1FinalOutput, Layer1KeyFacts, DimensionResult } from "@/lib/api";
import { getLayer1Output } from "@/lib/api";
import { RiskGauge } from "@/components/diagnostics/risk-gauge";
import { RiskBar } from "@/components/diagnostics/risk-bar";
import { DimensionCard } from "@/components/diagnostics/dimension-card";

type PageState = "loading" | "empty" | "ready" | "error";

const DIMENSION_ORDER: Array<{ key: keyof Layer1FinalOutput["dimensions"]; label: string }> = [
    { key: "data_integrity", label: "Data Integrity" },
    { key: "target_viability", label: "Target Viability" },
    { key: "sample_adequacy", label: "Sample Adequacy" },
];

function getDimensionLabel(key: string | null): string {
    return DIMENSION_ORDER.find((dimension) => dimension.key === key)?.label ?? "No failing dimension";
}

export default function Layer1ReportPage() {
    const [pageState, setPageState] = useState<PageState>("loading");
    const [data, setData] = useState<Layer1FinalOutput | null>(null);
    const [facts, setFacts] = useState<Layer1KeyFacts | null>(null);

    useEffect(() => {
        async function fetchData() {
            try {
                const response = await getLayer1Output();
                const output = response?.final_output;

                if (!output?.overall) {
                    setPageState("empty");
                    return;
                }

                setData(output);
                if (response?.logic?.facts) {
                    setFacts(response.logic.facts);
                }
                setPageState("ready");
            } catch {
                setPageState("empty");
            }
        }

        fetchData();
    }, []);

    const sortedDimensions = data
        ? DIMENSION_ORDER
            .map(({ key }) => ({
                key,
                dimension: data.dimensions[key] as DimensionResult,
            }))
            .filter((entry) => entry.dimension != null)
            .sort((left, right) => right.dimension.risk - left.dimension.risk)
        : [];

    if (pageState === "loading") {
        return (
            <main className="flex min-h-[calc(100vh-8rem)] flex-grow items-center justify-center">
                <div className="pointer-events-none absolute inset-0 z-0 bg-grid-pattern" />
                <div className="relative z-10 flex flex-col items-center gap-4">
                    <div className="size-12 animate-spin rounded-full border-2 border-primary/30 border-t-primary" />
                    <p className="text-sm font-mono tracking-wide text-muted-foreground">
                        Loading structural risk assessment...
                    </p>
                </div>
            </main>
        );
    }

    if (pageState === "empty" || !data) {
        return (
            <main className="flex min-h-[calc(100vh-8rem)] flex-grow items-center justify-center">
                <div className="pointer-events-none absolute inset-0 z-0 bg-grid-pattern" />
                <div className="relative z-10 flex flex-col items-center gap-6 px-6 text-center">
                    <div className="flex size-16 items-center justify-center rounded-full border border-white/10 bg-white/5">
                        <Activity className="size-8 text-muted-foreground" />
                    </div>
                    <div>
                        <h2 className="mb-2 text-xl font-semibold">No diagnostics report available.</h2>
                        <p className="text-sm font-mono text-muted-foreground">
                            Please run Layer 1 analysis first.
                        </p>
                    </div>
                    <Link
                        href={"/diagnostics" as Route}
                        className="inline-flex items-center gap-2 rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-primary/90"
                    >
                        Back to Diagnostics
                    </Link>
                </div>
            </main>
        );
    }

    const primaryFailureSource = getDimensionLabel(data.overall.primary_failure_source);
    const hasPrimaryFailure = Boolean(data.overall.primary_failure_source);
    const failingDimensionsText = `${data.overall.failing_dimensions} of ${data.overall.total_dimensions} dimensions failing`;

    return (
        <main className="relative flex min-h-[calc(100vh-8rem)] flex-grow flex-col">
            <div className="pointer-events-none absolute inset-0 z-0 bg-grid-pattern" />

            <section className="relative z-10 mx-auto flex w-full max-w-6xl flex-col gap-10 px-6 py-14 md:px-8">
                <div className="flex items-center gap-3">
                    <Link
                        href={"/diagnostics" as Route}
                        className="text-base font-mono text-muted-foreground transition-colors hover:text-foreground"
                    >
                        Diagnostics
                    </Link>
                    <span className="text-muted-foreground/40">/</span>
                    <span className="text-base font-mono text-foreground">
                        Structural Risk Assessment
                    </span>
                </div>

                <div>
                    <p className="text-base font-mono font-semibold tracking-wide text-muted-foreground">
                        Layer 1 - Structural Risk Assessment
                    </p>
                    <p className="mt-0.5 text-sm font-mono text-muted-foreground/75">
                        Signal to risk to aggregation to decision across three structural dimensions.
                    </p>
                </div>

                <div className="rounded-xl border border-white/[0.06] bg-card/60 p-8 backdrop-blur md:p-10">
                    <div className="flex flex-col items-center">
                        <h2 className="mb-6 text-xs font-mono font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                            Overall Structural Risk
                        </h2>

                        <RiskGauge
                            risk={data.overall.risk}
                            status={data.overall.status}
                        />

                        <div className="mt-8 w-full max-w-lg">
                            <RiskBar
                                risk={data.overall.risk}
                                height="h-2.5"
                                showMarker={true}
                                showLabels={true}
                            />
                        </div>

                        <div className="mt-8 w-full max-w-3xl rounded-2xl border border-white/8 bg-white/[0.03] p-5">
                            <p className="text-[10px] font-mono font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                                Primary Failure Source
                            </p>
                            <p className="mt-2 text-2xl font-semibold tracking-tight text-foreground">
                                {primaryFailureSource}
                            </p>
                            <p className="mt-3 text-sm text-muted-foreground">
                                {hasPrimaryFailure
                                    ? `Driven by ${primaryFailureSource}. ${failingDimensionsText}.`
                                    : `No failing dimension detected. All ${data.overall.total_dimensions} dimensions are currently safe.`}
                            </p>
                        </div>
                    </div>
                </div>

                {facts && (
                    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                        <div className="rounded-xl border border-white/[0.06] bg-card/60 p-5 backdrop-blur">
                            <div className="mb-4 flex items-center gap-2">
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

                        <div className="rounded-xl border border-white/[0.06] bg-card/60 p-5 backdrop-blur">
                            <div className="mb-4 flex items-center gap-2">
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

                        <div className="rounded-xl border border-white/[0.06] bg-card/60 p-5 backdrop-blur">
                            <div className="mb-4 flex items-center gap-2">
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

                <div>
                    <h2 className="mb-5 text-xs font-mono font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                        Structural Dimensions
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

                <div className="h-8" />
            </section>
        </main>
    );
}

function FactRow({ label, value }: { label: string; value: string }) {
    return (
        <div className="flex items-center justify-between">
            <span className="text-muted-foreground">{label}</span>
            <span className="font-medium text-foreground">{value}</span>
        </div>
    );
}
