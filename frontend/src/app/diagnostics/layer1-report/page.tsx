"use client";

import { useEffect, useState, type ReactNode } from "react";
import Link from "next/link";
import type { Route } from "next";
import clsx from "clsx";
import {
    Activity,
    ArrowRight,
    CheckCircle2,
    Columns3,
    Database,
    FileCheck2,
    HardDrive,
    ListChecks,
    OctagonX,
    ShieldCheck,
    TriangleAlert,
} from "lucide-react";
import { DimensionCard } from "@/components/diagnostics/dimension-card";
import type { Layer1FinalOutput, Layer1KeyFacts } from "@/lib/api";
import { getLayer1Output } from "@/lib/api";
import { useDiagnosticsStore } from "@/lib/diagnostics-store";
import {
    buildLayer1ValidationModel,
    type DecisionStatus,
    type ValidationCheck,
    type ValidationDecision,
    type ValidationStatus,
} from "@/lib/layer1-validation";

type PageState = "loading" | "empty" | "ready" | "error";

export default function Layer1ReportPage() {
    const cachedResult = useDiagnosticsStore((store) => store.analysisResult);

    const [pageState, setPageState] = useState<PageState>(
        cachedResult?.final_output?.overall ? "ready" : "loading",
    );
    const [data, setData] = useState<Layer1FinalOutput | null>(cachedResult?.final_output ?? null);
    const [facts, setFacts] = useState<Layer1KeyFacts | null>(
        cachedResult?.logic?.facts ?? null,
    );
    const [errorMessage, setErrorMessage] = useState("");

    useEffect(() => {
        if (cachedResult?.final_output?.overall) {
            return;
        }

        async function fetchData() {
            try {
                const response = await getLayer1Output();
                const output = response.final_output;

                if (!output?.overall) {
                    setPageState("empty");
                    return;
                }

                setData(output);
                setFacts(response.logic?.facts ?? null);
                setPageState("ready");
            } catch (error) {
                const message = error instanceof Error ? error.message : "Failed to load validation report.";
                setErrorMessage(message);
                setPageState(message.includes("No valid file") ? "empty" : "error");
            }
        }

        fetchData();
    }, [cachedResult]);

    if (pageState === "loading") {
        return (
            <main className="flex min-h-[calc(100vh-8rem)] flex-grow items-center justify-center">
                <div className="pointer-events-none absolute inset-0 z-0 bg-grid-pattern" />
                <div className="relative z-10 flex flex-col items-center gap-4">
                    <div className="size-12 animate-spin rounded-full border-2 border-primary/30 border-t-primary" />
                    <p className="font-mono text-sm tracking-wide text-muted-foreground">
                        Loading validation gate...
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
                    <div className="flex size-16 items-center justify-center rounded-lg border border-white/10 bg-white/5">
                        <Activity className="size-8 text-muted-foreground" />
                    </div>
                    <div>
                        <h2 className="mb-2 text-xl font-semibold">No validation report available.</h2>
                        <p className="font-mono text-sm text-muted-foreground">
                            {errorMessage || "Run Layer 1 validation first."}
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

    if (pageState === "error") {
        return (
            <main className="flex min-h-[calc(100vh-8rem)] flex-grow items-center justify-center">
                <div className="pointer-events-none absolute inset-0 z-0 bg-grid-pattern" />
                <div className="relative z-10 flex max-w-lg flex-col items-center gap-6 px-6 text-center">
                    <h2 className="text-xl font-semibold">Validation report could not be loaded.</h2>
                    <p className="font-mono text-sm text-red-400">
                        {errorMessage || "Unexpected error while loading the report."}
                    </p>
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

    const validation = buildLayer1ValidationModel(data, facts);

    return (
        <main className="relative flex min-h-[calc(100vh-8rem)] flex-grow flex-col">
            <div className="pointer-events-none absolute inset-0 z-0 bg-grid-pattern" />

            <section className="relative z-10 mx-auto flex w-full max-w-7xl flex-col gap-8 px-6 py-12 md:px-8">
                <div className="flex items-center gap-3">
                    <Link
                        href={"/diagnostics" as Route}
                        className="font-mono text-base text-muted-foreground transition-colors hover:text-foreground"
                    >
                        Diagnostics
                    </Link>
                    <span className="text-muted-foreground/40">/</span>
                    <span className="font-mono text-base text-foreground">
                        Structural Validation Gate
                    </span>
                </div>

                <div>
                    <p className="font-mono text-base font-semibold tracking-wide text-muted-foreground">
                        Layer 1 - Pre-model Validation Gate
                    </p>
                    <h1 className="mt-2 text-3xl font-bold tracking-tight text-foreground md:text-4xl">
                        Can this dataset proceed?
                    </h1>
                </div>

                <DecisionBanner decision={validation.decision} />

                <DecisionFlow decision={validation.decision} />

                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    <DecisionMetric
                        label="Failure Count"
                        value={validation.decision.failureCount}
                        tone={validation.decision.failureCount > 0 ? "fail" : "pass"}
                    />
                    <DecisionMetric
                        label="Blocker Count"
                        value={validation.decision.blockerCount}
                        tone={validation.decision.blockerCount > 0 ? "fail" : "pass"}
                    />
                    <DecisionMetric
                        label="Degradation Signals"
                        value={validation.decision.degradationCount}
                        tone={validation.decision.degradationCount > 0 ? "warning" : "pass"}
                    />
                    <DecisionMetric
                        label="Checks Run"
                        value={validation.decision.checksRun}
                        tone="neutral"
                    />
                </div>

                {facts && <DatasetEvidence facts={facts} />}

                <FailureBreakdown failures={validation.failures} />

                {validation.warnings.length > 0 && (
                    <ActionLayer title="Conditional Warning Actions" checks={validation.warnings} />
                )}

                <div>
                    <h2 className="mb-5 font-mono text-xs font-bold uppercase tracking-[0.2em] text-muted-foreground">
                        Section: Validation Checks
                    </h2>

                    <div className="space-y-4">
                        {validation.sections.map((section) => (
                            <DimensionCard key={section.key} section={section} />
                        ))}
                    </div>
                </div>

                <div className="h-8" />
            </section>
        </main>
    );
}

function DecisionBanner({ decision }: { decision: ValidationDecision }) {
    const styles = getDecisionStyles(decision.status);
    const Icon = decision.status === "BLOCKED"
        ? OctagonX
        : decision.status === "CONDITIONALLY ALLOWED"
            ? TriangleAlert
            : ShieldCheck;

    return (
        <section className={clsx("rounded-lg border p-6 md:p-8", styles.panel)}>
            <div className="flex flex-col gap-5 md:flex-row md:items-start md:justify-between">
                <div className="flex gap-4">
                    <div className={clsx("flex size-12 shrink-0 items-center justify-center rounded-md border", styles.icon)}>
                        <Icon className="size-7" />
                    </div>
                    <div>
                        <p className="font-mono text-[10px] font-bold uppercase tracking-[0.24em] text-muted-foreground">
                            System Decision
                        </p>
                        <h2 className={clsx("mt-2 text-3xl font-black uppercase tracking-tight md:text-5xl", styles.text)}>
                            {decision.status}
                        </h2>
                        <p className="mt-3 text-lg font-semibold text-foreground">
                            {decision.message}
                        </p>
                        <p className="mt-2 font-mono text-sm text-muted-foreground">
                            {decision.summary}
                        </p>
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-3 font-mono text-xs md:min-w-72">
                    <BannerFact label="Confidence" value={decision.confidence} />
                    <BannerFact label="Gate Mode" value="Deterministic" />
                </div>
            </div>
        </section>
    );
}

function DecisionFlow({ decision }: { decision: ValidationDecision }) {
    const checkStatus: ValidationStatus = decision.status === "BLOCKED"
        ? "FAIL"
        : decision.status === "CONDITIONALLY ALLOWED"
            ? "WARNING"
            : "PASS";
    const finalStatus: ValidationStatus = checkStatus;

    const steps: Array<{ label: string; caption: string; status: ValidationStatus }> = [
        { label: "Raw Data", caption: "Loaded", status: "PASS" },
        { label: "Structural Checks", caption: `${decision.checksRun} checks`, status: checkStatus },
        { label: "Validation Decisions", caption: decision.summary, status: checkStatus },
        { label: "Final Gate", caption: decision.status, status: finalStatus },
    ];

    return (
        <section className="rounded-lg border border-white/[0.08] bg-card/60 p-5 backdrop-blur md:p-6">
            <div className="mb-5 flex items-center gap-2">
                <ListChecks className="size-4 text-primary" />
                <h2 className="font-mono text-xs font-bold uppercase tracking-[0.2em] text-muted-foreground">
                    Decision Flow
                </h2>
            </div>

            <div className="grid gap-3 md:grid-cols-[1fr_auto_1fr_auto_1fr_auto_1fr] md:items-stretch">
                {steps.map((step, index) => (
                    <div key={step.label} className="contents">
                        <FlowStep step={step} />
                        {index < steps.length - 1 && (
                            <div className="hidden items-center justify-center md:flex">
                                <ArrowRight className="size-5 text-muted-foreground" />
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </section>
    );
}

function FlowStep({ step }: { step: { label: string; caption: string; status: ValidationStatus } }) {
    const styles = getStatusStyles(step.status);
    const Icon = step.status === "FAIL" ? OctagonX : step.status === "WARNING" ? TriangleAlert : CheckCircle2;

    return (
        <div className={clsx("rounded-lg border p-4", styles.panel)}>
            <div className="flex items-start gap-3">
                <Icon className={clsx("mt-0.5 size-5 shrink-0", styles.text)} />
                <div>
                    <p className="font-semibold text-foreground">{step.label}</p>
                    <p className="mt-1 font-mono text-xs text-muted-foreground">{step.caption}</p>
                </div>
            </div>
        </div>
    );
}

function DecisionMetric({
    label,
    value,
    tone,
}: {
    label: string;
    value: number;
    tone: "fail" | "warning" | "pass" | "neutral";
}) {
    const className = tone === "fail"
        ? "border-red-500/35 bg-red-500/10 text-red-300"
        : tone === "warning"
            ? "border-yellow-500/35 bg-yellow-500/10 text-yellow-200"
            : tone === "pass"
                ? "border-green-500/30 bg-green-500/10 text-green-300"
                : "border-white/[0.08] bg-card/60 text-foreground";

    return (
        <div className={clsx("rounded-lg border p-5 font-mono backdrop-blur", className)}>
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-muted-foreground">
                {label}
            </p>
            <p className="mt-3 text-3xl font-black tabular-nums">{value}</p>
        </div>
    );
}

function DatasetEvidence({ facts }: { facts: Layer1KeyFacts }) {
    const samplesPerFeature = facts.dimensions.columns > 0
        ? facts.dimensions.rows / facts.dimensions.columns
        : 0;

    return (
        <section>
            <h2 className="mb-4 font-mono text-xs font-bold uppercase tracking-[0.2em] text-muted-foreground">
                Observed Dataset Evidence
            </h2>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                <EvidencePanel icon={Database} title="Dataset">
                    <FactRow label="Shape" value={facts.dimensions.shape} />
                    <FactRow label="Rows" value={facts.dimensions.rows.toLocaleString()} />
                    <FactRow label="Columns" value={String(facts.dimensions.columns)} />
                    <FactRow label="Samples / Feature" value={samplesPerFeature.toFixed(2)} />
                </EvidencePanel>

                <EvidencePanel icon={HardDrive} title="Memory">
                    <FactRow label="Usage" value={`${facts.memory.memory_mb} MB`} />
                    <FactRow label="Class" value={facts.memory.memory_class} />
                </EvidencePanel>

                <EvidencePanel icon={Columns3} title="Feature Mix">
                    <FactRow label="Type" value={facts.feature_mix.mix_type} />
                    <FactRow label="Numeric Columns" value={`${(facts.feature_mix.num_ratio * 100).toFixed(0)}%`} />
                    <FactRow label="Categorical Columns" value={`${(facts.feature_mix.cat_ratio * 100).toFixed(0)}%`} />
                </EvidencePanel>
            </div>
        </section>
    );
}

function EvidencePanel({
    icon: Icon,
    title,
    children,
}: {
    icon: typeof Database;
    title: string;
    children: ReactNode;
}) {
    return (
        <div className="rounded-lg border border-white/[0.08] bg-card/60 p-5 backdrop-blur">
            <div className="mb-4 flex items-center gap-2">
                <Icon className="size-4 text-primary" />
                <h3 className="font-mono text-xs font-bold uppercase tracking-widest text-muted-foreground">
                    {title}
                </h3>
            </div>
            <div className="space-y-2.5 font-mono text-sm">
                {children}
            </div>
        </div>
    );
}

function FailureBreakdown({ failures }: { failures: ValidationCheck[] }) {
    if (failures.length === 0) {
        return (
            <section className="rounded-lg border border-green-500/30 bg-green-500/10 p-5 md:p-6">
                <div className="flex gap-3">
                    <FileCheck2 className="mt-0.5 size-5 shrink-0 text-green-300" />
                    <div>
                        <h2 className="font-mono text-xs font-bold uppercase tracking-[0.2em] text-green-300">
                            Failure Breakdown
                        </h2>
                        <p className="mt-2 text-sm text-foreground">
                            No failed tests. Dataset passed the structural validation gate.
                        </p>
                    </div>
                </div>
            </section>
        );
    }

    return (
        <section>
            <h2 className="mb-4 font-mono text-xs font-bold uppercase tracking-[0.2em] text-muted-foreground">
                Failure Breakdown
            </h2>
            <div className="space-y-3">
                {failures.map((failure) => (
                    <FailureItem key={failure.id} failure={failure} />
                ))}
            </div>
        </section>
    );
}

function FailureItem({ failure }: { failure: ValidationCheck }) {
    return (
        <article className="rounded-lg border border-red-500/35 bg-red-500/10 p-5">
            <div className="mb-4 flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                <div>
                    <p className="font-mono text-[10px] font-bold uppercase tracking-[0.2em] text-red-300">
                        Failure: {failure.testName}
                    </p>
                    <h3 className="mt-1 text-lg font-semibold text-foreground">
                        {failure.dimensionLabel}
                    </h3>
                </div>
                <span className="w-fit rounded-md border border-red-500 px-2 py-1 font-mono text-[10px] font-bold uppercase tracking-widest text-red-300">
                    {failure.impact}
                </span>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
                <BreakdownField label="What failed" value={`${failure.observed}; threshold ${failure.threshold}`} />
                <BreakdownField label="Why it failed" value={failure.reason} />
                <BreakdownField label="Rule violated" value={failure.rule} />
                <BreakdownField label="Direct action" value={failure.action} />
            </div>

            <div className="mt-4 rounded-md border border-red-500/25 bg-black/20 p-3">
                <p className="mb-2 font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-red-300">
                    Exact Offending Columns
                </p>
                {failure.offendingColumns.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                        {failure.offendingColumns.map((column) => (
                            <span
                                key={column}
                                className="rounded-md border border-red-500/30 px-2 py-1 font-mono text-xs text-foreground"
                            >
                                {column}
                            </span>
                        ))}
                    </div>
                ) : (
                    <p className="font-mono text-xs text-muted-foreground">
                        No single offending column reported; this failure is dataset-level.
                    </p>
                )}
            </div>
        </article>
    );
}

function ActionLayer({ title, checks }: { title: string; checks: ValidationCheck[] }) {
    return (
        <section className="rounded-lg border border-yellow-500/35 bg-yellow-500/10 p-5 md:p-6">
            <div className="mb-4 flex items-center gap-2">
                <TriangleAlert className="size-4 text-yellow-200" />
                <h2 className="font-mono text-xs font-bold uppercase tracking-[0.2em] text-yellow-200">
                    {title}
                </h2>
            </div>
            <div className="space-y-3">
                {checks.map((check) => (
                    <div key={check.id} className="rounded-md border border-yellow-500/25 bg-black/15 p-3">
                        <p className="font-semibold text-foreground">
                            {check.dimensionLabel}: {check.testName}
                        </p>
                        <p className="mt-1 text-sm text-muted-foreground">
                            {check.optionalAction ?? check.action}
                        </p>
                    </div>
                ))}
            </div>
        </section>
    );
}

function BreakdownField({ label, value }: { label: string; value: string }) {
    return (
        <div>
            <p className="mb-1 font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
                {label}
            </p>
            <p className="text-sm leading-relaxed text-foreground">{value}</p>
        </div>
    );
}

function BannerFact({ label, value }: { label: string; value: string }) {
    return (
        <div className="rounded-md border border-white/[0.08] bg-black/20 px-3 py-2">
            <p className="text-[10px] uppercase tracking-widest text-muted-foreground">{label}</p>
            <p className="mt-1 text-sm font-bold text-foreground">{value}</p>
        </div>
    );
}

function FactRow({ label, value }: { label: string; value: string }) {
    return (
        <div className="flex items-center justify-between gap-4">
            <span className="text-muted-foreground">{label}</span>
            <span className="font-medium text-foreground">{value}</span>
        </div>
    );
}

function getDecisionStyles(status: DecisionStatus) {
    if (status === "BLOCKED") {
        return {
            panel: "border-red-500/45 bg-red-500/10",
            icon: "border-red-500/50 bg-red-500/10 text-red-300",
            text: "text-red-300",
        };
    }
    if (status === "CONDITIONALLY ALLOWED") {
        return {
            panel: "border-yellow-500/45 bg-yellow-500/10",
            icon: "border-yellow-500/50 bg-yellow-500/10 text-yellow-200",
            text: "text-yellow-200",
        };
    }
    return {
        panel: "border-green-500/40 bg-green-500/10",
        icon: "border-green-500/45 bg-green-500/10 text-green-300",
        text: "text-green-300",
    };
}

function getStatusStyles(status: ValidationStatus) {
    if (status === "FAIL") {
        return {
            panel: "border-red-500/35 bg-red-500/10",
            text: "text-red-300",
        };
    }
    if (status === "WARNING") {
        return {
            panel: "border-yellow-500/35 bg-yellow-500/10",
            text: "text-yellow-200",
        };
    }
    return {
        panel: "border-green-500/30 bg-green-500/10",
        text: "text-green-300",
    };
}
