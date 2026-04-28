"use client";

import { useEffect, useState, type ReactNode } from "react";
import Link from "next/link";
import type { Route } from "next";
import clsx from "clsx";
import {
    Activity,
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
                <div className="relative z-10 flex flex-col items-center gap-6 px-6 text-center">
                    <div className="flex size-16 items-center justify-center rounded-lg border border-border bg-card">
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
                        className="inline-flex items-center gap-2 rounded-lg border border-border bg-card px-6 py-2.5 text-sm font-medium text-foreground transition-colors hover:bg-background"
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
                <div className="relative z-10 flex max-w-lg flex-col items-center gap-6 px-6 text-center">
                    <h2 className="text-xl font-semibold">Validation report could not be loaded.</h2>
                    <p className="font-mono text-sm text-red-500">
                        {errorMessage || "Unexpected error while loading the report."}
                    </p>
                    <Link
                        href={"/diagnostics" as Route}
                        className="inline-flex items-center gap-2 rounded-lg border border-border bg-card px-6 py-2.5 text-sm font-medium text-foreground transition-colors hover:bg-background"
                    >
                        Back to Diagnostics
                    </Link>
                </div>
            </main>
        );
    }

    const validation = buildLayer1ValidationModel(data, facts);

    return (
        <main className="diagnostic-gate diag-page relative flex min-h-[calc(100vh-8rem)] flex-grow flex-col">
            <section className="relative z-10 mx-auto flex w-full max-w-[1480px] flex-col gap-6 px-4 py-7 md:px-7">
                <div className="flex items-center gap-3 border-b pb-4 [border-color:var(--diag-border)]">
                    <Link
                        href={"/diagnostics" as Route}
                        className="diag-muted font-mono text-xs uppercase tracking-[0.18em] transition-colors hover:text-[var(--diag-strong)]"
                    >
                        Diagnostics
                    </Link>
                    <span className="diag-muted-soft font-mono">/</span>
                    <span className="diag-text font-mono text-xs uppercase tracking-[0.18em]">
                        Structural Validation Gate
                    </span>
                </div>

                <div className="grid gap-4 lg:grid-cols-[1fr_auto] lg:items-end">
                    <div>
                        <p className="diag-muted font-mono text-[11px] font-semibold uppercase tracking-[0.28em]">
                            Layer 1 - Pre-model Validation Gate
                        </p>
                        <h1 className="diag-strong mt-2 text-3xl font-bold tracking-tight md:text-5xl">
                            Can this dataset proceed?
                        </h1>
                    </div>
                    <div className="diag-muted grid grid-cols-1 gap-2 font-mono text-[10px] uppercase tracking-[0.16em] sm:grid-cols-3">
                        <span className="diag-chip rounded border px-3 py-2">Gate deterministic</span>
                        <span className="diag-chip rounded border px-3 py-2">Layer 1 only</span>
                        <span className="diag-chip rounded border px-3 py-2">No model fit</span>
                    </div>
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
                    <h2 className="diag-muted mb-5 font-mono text-xs font-bold uppercase tracking-[0.2em]">
                        Section: Validation Checks
                    </h2>

                    <div className="space-y-4">
                        {validation.sections.map((section) => (
                            <DimensionCard key={section.key} section={section} />
                        ))}
                    </div>
                </div>

                <div className="h-5" />
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
        <section className={clsx("diag-panel rounded-md border border-l-4 p-5 shadow-[0_0_0_1px_rgba(255,255,255,0.015)] md:p-6", styles.panel)}>
            <div className="flex flex-col gap-5 md:flex-row md:items-start md:justify-between">
                <div className="flex gap-4">
                    <div className="diag-body flex size-12 shrink-0 items-center justify-center rounded border [border-color:var(--diag-border)]">
                        <Icon className={clsx("size-7", styles.icon)} />
                    </div>
                    <div>
                        <p className="diag-muted font-mono text-[10px] font-bold uppercase tracking-[0.24em]">
                            System Decision
                        </p>
                        <h2 className="diag-strong mt-2 text-3xl font-black uppercase tracking-tight md:text-5xl">
                            {decision.status}
                        </h2>
                        <p className="diag-text mt-3 text-lg font-semibold">
                            {decision.message}
                        </p>
                        <p className="diag-muted mt-2 font-mono text-sm">
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
        <section className="diag-panel rounded-md border p-4 md:p-5">
            <div className="mb-5 flex items-center gap-2">
                <ListChecks className="diag-muted size-4" />
                <h2 className="diag-muted font-mono text-xs font-bold uppercase tracking-[0.2em]">
                    Decision Flow
                </h2>
            </div>

            <div className="grid gap-4 md:grid-cols-4 md:items-start">
                {steps.map((step, index) => (
                    <FlowStep key={step.label} step={step} isLast={index === steps.length - 1} />
                ))}
            </div>
        </section>
    );
}

function FlowStep({ step, isLast }: { step: { label: string; caption: string; status: ValidationStatus }; isLast: boolean }) {
    const styles = getStatusStyles(step.status);

    return (
        <div className="relative">
            {!isLast && (
                <div className="absolute left-[13px] top-[15px] hidden h-px w-[calc(100%+1rem)] md:block [background-color:var(--diag-border)]" />
            )}
            <div className="relative flex items-start gap-3">
                <span className={clsx("mt-1 size-3 shrink-0 rounded-full ring-4", styles.dot)} />
                <div>
                    <p className="diag-muted font-mono text-[10px] font-semibold uppercase tracking-[0.18em]">{step.label}</p>
                    <p className="diag-text mt-2 text-sm font-semibold">{step.caption}</p>
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
        ? "diag-fail-panel"
        : tone === "warning"
            ? "diag-warn-panel"
            : tone === "pass"
                ? "diag-pass-panel"
                : "diag-panel";

    return (
        <div className={clsx("rounded-md border p-4 font-mono", className)}>
            <p className="diag-muted text-[10px] font-bold uppercase tracking-[0.2em]">
                {label}
            </p>
            <p className="diag-strong mt-3 font-sans text-3xl font-black tabular-nums">{value}</p>
        </div>
    );
}

function DatasetEvidence({ facts }: { facts: Layer1KeyFacts }) {
    const samplesPerFeature = facts.dimensions.columns > 0
        ? facts.dimensions.rows / facts.dimensions.columns
        : 0;

    return (
        <section>
            <h2 className="diag-muted mb-4 font-mono text-xs font-bold uppercase tracking-[0.2em]">
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
        <div className="diag-panel rounded-md border p-4">
            <div className="mb-4 flex items-center gap-2">
                <Icon className="diag-muted size-4" />
                <h3 className="diag-muted font-mono text-xs font-bold uppercase tracking-widest">
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
            <section className="diag-panel rounded-md border border-l-4 border-l-green-500 p-5 md:p-6">
                <div className="flex gap-3">
                    <FileCheck2 className="mt-0.5 size-5 shrink-0 text-green-500" />
                    <div>
                        <h2 className="diag-muted font-mono text-xs font-bold uppercase tracking-[0.2em]">
                            Failure Breakdown
                        </h2>
                        <p className="diag-text mt-2 text-sm">
                            No failed tests. Dataset passed the structural validation gate.
                        </p>
                    </div>
                </div>
            </section>
        );
    }

    return (
        <section>
            <h2 className="diag-muted mb-4 font-mono text-xs font-bold uppercase tracking-[0.2em]">
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
        <article className={clsx(
            "diag-body overflow-hidden rounded-md border border-l-4",
            failure.impact === "BLOCKER"
                ? "diag-fail-panel border-l-[#e24b4a]"
                : "diag-warn-panel border-l-[#d4901a]",
        )}>
            <div className={clsx(
                "flex flex-col gap-2 px-5 py-4 md:flex-row md:items-start md:justify-between",
                failure.impact === "BLOCKER" ? "diag-fail-header" : "diag-warn-header",
            )}>
                <div>
                    <p className={clsx(
                        "font-mono text-[10px] font-bold uppercase tracking-[0.2em]",
                        failure.impact === "BLOCKER" ? "text-[#e24b4a]" : "text-[#d4901a]",
                    )}>
                        Failure: {failure.testName}
                    </p>
                    <h3 className="diag-strong mt-1 text-lg font-semibold">
                        {failure.dimensionLabel}
                    </h3>
                </div>
                <span className={clsx(
                    "w-fit rounded border px-2 py-1 font-mono text-[10px] font-bold uppercase tracking-widest",
                    failure.impact === "BLOCKER"
                        ? "border-[#e24b4a]/40 bg-[#e24b4a]/10 text-[#ff7775]"
                        : "border-[#d4901a]/40 bg-[#d4901a]/10 text-[#e9ad43]",
                )}>
                    {failure.impact}
                </span>
            </div>

            <div className="diag-body grid gap-4 p-5 md:grid-cols-2">
                <BreakdownField label="What failed" value={`${failure.observed}; threshold ${failure.threshold}`} />
                <BreakdownField label="Why it failed" value={failure.reason} />
                <BreakdownField label="Rule violated" value={failure.rule} />
                <BreakdownField label="Direct action" value={failure.action} />
            </div>

            <div className="diag-body border-t p-5 pt-4 [border-color:var(--diag-border)]">
                <p className="diag-muted mb-2 font-mono text-[10px] font-bold uppercase tracking-[0.18em]">
                    Exact Offending Columns
                </p>
                {failure.offendingColumns.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                        {failure.offendingColumns.map((column) => (
                            <span
                                key={column}
                                className="diag-panel rounded border px-2 py-1 font-mono text-xs"
                            >
                                {column}
                            </span>
                        ))}
                    </div>
                ) : (
                    <p className="diag-muted font-mono text-xs">
                        No single offending column reported; this failure is dataset-level.
                    </p>
                )}
            </div>
        </article>
    );
}

function ActionLayer({ title, checks }: { title: string; checks: ValidationCheck[] }) {
    return (
        <section className="diag-panel rounded-md border border-l-4 border-l-[#d4901a] p-5 md:p-6">
            <div className="mb-4 flex items-center gap-2">
                <TriangleAlert className="size-4 text-[#d4901a]" />
                <h2 className="diag-muted font-mono text-xs font-bold uppercase tracking-[0.2em]">
                    {title}
                </h2>
            </div>
            <div className="space-y-3">
                {checks.map((check) => (
                    <div key={check.id} className="diag-row rounded border p-3">
                        <p className="diag-text font-semibold">
                            {check.dimensionLabel}: {check.testName}
                        </p>
                        <p className="diag-muted mt-1 text-sm">
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
            <p className="diag-muted mb-1 font-mono text-[10px] font-bold uppercase tracking-[0.18em]">
                {label}
            </p>
            <p className="diag-text text-sm leading-relaxed">{value}</p>
        </div>
    );
}

function BannerFact({ label, value }: { label: string; value: string }) {
    return (
        <div className="diag-body rounded border px-3 py-2 [border-color:var(--diag-border)]">
            <p className="diag-muted text-[10px] uppercase tracking-widest">{label}</p>
            <p className="diag-strong mt-1 text-sm font-bold">{value}</p>
        </div>
    );
}

function FactRow({ label, value }: { label: string; value: string }) {
    return (
        <div className="flex items-center justify-between gap-4">
            <span className="diag-muted">{label}</span>
            <span className="diag-strong font-sans font-semibold">{value}</span>
        </div>
    );
}

function getDecisionStyles(status: DecisionStatus) {
    if (status === "BLOCKED") {
        return {
            panel: "diag-fail-panel border-l-[#e24b4a]",
            icon: "text-[#e24b4a]",
        };
    }
    if (status === "CONDITIONALLY ALLOWED") {
        return {
            panel: "diag-warn-panel border-l-[#d4901a]",
            icon: "text-[#d4901a]",
        };
    }
    return {
        panel: "border-l-green-500",
        icon: "text-green-500",
    };
}

function getStatusStyles(status: ValidationStatus) {
    if (status === "FAIL") {
        return {
            icon: "text-red-500",
            dot: "bg-[#e24b4a] shadow-[0_0_14px_rgba(226,75,74,0.72)] ring-[#e24b4a]/10",
        };
    }
    if (status === "WARNING") {
        return {
            icon: "text-amber-500",
            dot: "bg-[#d4901a] shadow-[0_0_14px_rgba(212,144,26,0.64)] ring-[#d4901a]/10",
        };
    }
    return {
        icon: "text-green-500",
        dot: "bg-green-500 shadow-[0_0_14px_rgba(34,197,94,0.64)] ring-green-500/10",
    };
}
