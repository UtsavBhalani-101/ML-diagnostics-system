"use client";

import { useState } from "react";
import clsx from "clsx";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Shield, Database, Target, BarChart3 } from "lucide-react";
import type { DimensionResult, PrimaryIssue } from "@/lib/api";
import { RiskBar } from "./risk-bar";
import { RiskBreakdownChart } from "./risk-breakdown-chart";
import { SignalTable } from "./signal-table";
import {
    Tooltip,
    TooltipContent,
    TooltipTrigger,
} from "@/components/ui/tooltip";

interface DimensionCardProps {
    name: string;
    dimension: DimensionResult;
    defaultExpanded?: boolean;
    className?: string;
}

interface SignalPreviewItem {
    label: string;
    value: string;
}

const DIMENSION_META: Record<string, {
    label: string;
    description: string;
    icon: typeof Shield;
}> = {
    data_integrity: {
        label: "Data Integrity",
        description: "Structural completeness and consistency of the raw data.",
        icon: Shield,
    },
    target_viability: {
        label: "Target Viability",
        description: "Whether the target is usable for reliable supervised learning.",
        icon: Target,
    },
    sample_adequacy: {
        label: "Sample Adequacy",
        description: "Whether the dataset has enough sample support for its feature space.",
        icon: BarChart3,
    },
};

function getStatusStyles(status: string) {
    const normalized = status.toUpperCase();
    if (normalized === "CRITICAL") {
        return {
            bg: "bg-red-500/10",
            border: "border-red-500/20",
            borderHover: "hover:border-red-500/35",
            text: "text-red-400",
            dot: "bg-red-500",
            badge: "bg-red-500/15 text-red-400 border-red-500/25",
        };
    }
    if (normalized === "WARNING") {
        return {
            bg: "bg-amber-500/10",
            border: "border-amber-500/20",
            borderHover: "hover:border-amber-500/35",
            text: "text-amber-400",
            dot: "bg-amber-500",
            badge: "bg-amber-500/15 text-amber-400 border-amber-500/25",
        };
    }
    return {
        bg: "bg-emerald-500/10",
        border: "border-emerald-500/20",
        borderHover: "hover:border-emerald-500/35",
        text: "text-emerald-400",
        dot: "bg-emerald-500",
        badge: "bg-emerald-500/15 text-emerald-400 border-emerald-500/25",
    };
}

function formatRiskName(key: string): string {
    const labels: Record<string, string> = {
        mixed_types: "Mixed Types",
        hidden_missing: "Hidden Missing",
        missing_values: "Missing Values",
        constant_columns: "Constant Columns",
        low_sample: "Low Sample Support",
        sample_size: "Sample Size",
        task_uncertainty: "Task Uncertainty",
        target_mixed_type: "Mixed Target Types",
        target_missing: "Missing Target Values",
        target_variance: "Low Target Variability",
        imbalance: "Class Imbalance",
        variance: "Low Variability",
        duplicates: "Duplicates",
    };

    return labels[key] ?? key.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatMetricValue(value: unknown): string {
    if (value === null || value === undefined) {
        return "None";
    }
    if (typeof value === "number") {
        if (Math.abs(value) <= 1 && !Number.isInteger(value)) {
            return `${(value * 100).toFixed(1)}%`;
        }
        if (Number.isInteger(value)) {
            return value.toLocaleString();
        }
        return value.toFixed(2);
    }
    if (typeof value === "boolean") {
        return value ? "Yes" : "No";
    }
    if (Array.isArray(value)) {
        if (value.length === 0) {
            return "None";
        }
        return value.slice(0, 3).join(", ");
    }
    return String(value);
}

function getTopNumericEntry(value: unknown): [string, number] | null {
    if (!value || typeof value !== "object" || Array.isArray(value)) {
        return null;
    }

    let best: [string, number] | null = null;
    for (const [key, entryValue] of Object.entries(value as Record<string, unknown>)) {
        if (typeof entryValue !== "number") {
            continue;
        }
        if (!best || entryValue > best[1]) {
            best = [key, entryValue];
        }
    }

    return best && best[1] > 0 ? best : null;
}

function buildSignalPreview(name: string, signals: Record<string, unknown>): SignalPreviewItem[] {
    const preview: SignalPreviewItem[] = [];

    if (name === "data_integrity") {
        const mixedColumns = Array.isArray(signals.mixed_type_columns) ? signals.mixed_type_columns : [];
        if (mixedColumns.length > 0) {
            preview.push({
                label: "Mixed-Type Columns",
                value: mixedColumns.slice(0, 3).join(", "),
            });
        }

        const highestMissing = getTopNumericEntry(signals.column_missing_ratio);
        if (highestMissing) {
            preview.push({
                label: "Highest Missing Column",
                value: `${highestMissing[0]} (${(highestMissing[1] * 100).toFixed(1)}%)`,
            });
        }

        if (typeof signals.global_missing_ratio === "number" && signals.global_missing_ratio > 0) {
            preview.push({
                label: "Global Missing",
                value: `${(signals.global_missing_ratio * 100).toFixed(1)}%`,
            });
        }

        if (typeof signals.duplicate_ratio === "number" && signals.duplicate_ratio > 0) {
            preview.push({
                label: "Duplicate Rows",
                value: `${(signals.duplicate_ratio * 100).toFixed(1)}%`,
            });
        }

        if (typeof signals.constant_ratio === "number" && signals.constant_ratio > 0) {
            preview.push({
                label: "Constant Columns",
                value: `${(signals.constant_ratio * 100).toFixed(1)}%`,
            });
        }
    }

    if (name === "target_viability") {
        if (typeof signals.target_missing_ratio === "number") {
            preview.push({
                label: "Target Missing",
                value: `${(signals.target_missing_ratio * 100).toFixed(1)}%`,
            });
        }

        if (typeof signals.target_unique_count === "number") {
            preview.push({
                label: "Unique Target Values",
                value: signals.target_unique_count.toLocaleString(),
            });
        }

        if (typeof signals.task_confidence === "number") {
            preview.push({
                label: "Task Confidence",
                value: `${(signals.task_confidence * 100).toFixed(0)}%`,
            });
        }

        if (typeof signals.class_imbalance_score === "number" && signals.class_imbalance_score > 0) {
            preview.push({
                label: "Imbalance Score",
                value: signals.class_imbalance_score.toFixed(2),
            });
        }
    }

    if (name === "sample_adequacy") {
        if (typeof signals.sample_feature_ratio === "number") {
            preview.push({
                label: "Samples per Feature",
                value: signals.sample_feature_ratio.toFixed(2),
            });
        }

        if (typeof signals.rows === "number") {
            preview.push({
                label: "Rows",
                value: signals.rows.toLocaleString(),
            });
        }

        if (typeof signals.cols === "number") {
            preview.push({
                label: "Columns",
                value: signals.cols.toLocaleString(),
            });
        }
    }

    if (preview.length > 0) {
        return preview.slice(0, 3);
    }

    return Object.entries(signals)
        .filter(([, value]) => typeof value !== "object")
        .slice(0, 3)
        .map(([label, value]) => ({
            label: formatRiskName(label),
            value: formatMetricValue(value),
        }));
}

function getMaterialPrimaryIssues(
    issues: PrimaryIssue[],
    status: string,
): PrimaryIssue[] {
    if (status !== "SAFE") {
        return issues.slice(0, 2);
    }

    return issues.filter((issue) => issue.risk >= 0.1).slice(0, 2);
}

export function DimensionCard({
    name,
    dimension,
    defaultExpanded = false,
    className,
}: DimensionCardProps) {
    const [expanded, setExpanded] = useState(defaultExpanded);
    const meta = DIMENSION_META[name] ?? {
        label: name.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase()),
        description: "",
        icon: Database,
    };
    const styles = getStatusStyles(dimension.status);
    const Icon = meta.icon;
    const materialIssues = getMaterialPrimaryIssues(dimension.primary_issues, dimension.status);
    const previewSignals = buildSignalPreview(name, dimension.signals);
    const hasSignalDetails = Object.keys(dimension.signals).length > 0;
    const hasBreakdown =
        [...Object.values(dimension.breakdown.dominant), ...Object.values(dimension.breakdown.additive)]
            .some((value) => value > 0);

    return (
        <div
            className={clsx(
                "rounded-xl border bg-card/60 backdrop-blur transition-all duration-300",
                styles.border,
                styles.borderHover,
                expanded && styles.bg,
                className,
            )}
        >
            <div
                role="button"
                tabIndex={0}
                onClick={() => setExpanded(!expanded)}
                onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        setExpanded(!expanded);
                    }
                }}
                className="flex w-full cursor-pointer items-center gap-4 p-5 text-left group md:p-6"
            >
                <div className={clsx("flex size-10 shrink-0 items-center justify-center rounded-lg", styles.bg)}>
                    <Icon className={clsx("size-5", styles.text)} />
                </div>

                <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2.5">
                        <h3 className="truncate text-base font-semibold tracking-tight">
                            {meta.label}
                        </h3>
                        <span
                            className={clsx(
                                "inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[10px] font-mono font-semibold uppercase tracking-widest",
                                styles.badge,
                            )}
                        >
                            <span className={clsx("size-1.5 rounded-full", styles.dot)} />
                            {dimension.status.toUpperCase()}
                        </span>
                    </div>
                    <div className="mt-2.5 max-w-48">
                        <RiskBar risk={dimension.risk} height="h-1.5" showMarker={false} />
                    </div>
                </div>

                <Tooltip>
                    <TooltipTrigger
                        className={clsx(
                            "shrink-0 text-2xl font-bold tabular-nums tracking-tight md:text-3xl",
                            styles.text,
                        )}
                    >
                        {dimension.risk.toFixed(2)}
                    </TooltipTrigger>
                    <TooltipContent side="left" className="max-w-48 text-xs">
                        <p className="font-medium">Risk Score</p>
                        <p className="mt-0.5 text-muted-foreground">
                            Higher values indicate more structural risk in this dimension.
                        </p>
                    </TooltipContent>
                </Tooltip>

                <ChevronDown
                    className={clsx(
                        "size-5 shrink-0 text-muted-foreground transition-transform duration-300",
                        expanded && "rotate-180",
                    )}
                />
            </div>

            <AnimatePresence initial={false}>
                {expanded && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3, ease: "easeInOut" }}
                        className="overflow-hidden"
                    >
                        <div className="space-y-6 px-5 pb-6 md:px-6">
                            <div className="border-t border-white/[0.06]" />

                            {meta.description && (
                                <p className="text-sm text-muted-foreground/80">
                                    {meta.description}
                                </p>
                            )}

                            <div className="grid gap-4 md:grid-cols-2">
                                <div className="rounded-xl border border-white/8 bg-white/[0.03] p-4">
                                    <p className="text-[10px] font-mono font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                                        Primary Issue
                                    </p>
                                    <div className="mt-3 space-y-2">
                                        {materialIssues.length > 0 ? (
                                            materialIssues.map((issue) => (
                                                <div key={`issue-${issue.name}`} className="flex items-center justify-between gap-3">
                                                    <span className="text-sm font-medium text-foreground">
                                                        {formatRiskName(issue.name)}
                                                    </span>
                                                    <span className="text-xs font-mono text-muted-foreground">
                                                        {issue.risk.toFixed(2)}
                                                    </span>
                                                </div>
                                            ))
                                        ) : (
                                            <p className="text-sm text-foreground">No material structural issue</p>
                                        )}
                                    </div>
                                </div>

                                <div className="rounded-xl border border-white/8 bg-white/[0.03] p-4">
                                    <p className="text-[10px] font-mono font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                                        Quick Action
                                    </p>
                                    <div className="mt-3 space-y-2">
                                        {materialIssues.length > 0 ? (
                                            materialIssues.map((issue) => (
                                                <p key={`action-${issue.name}`} className="text-sm text-foreground">
                                                    {issue.action}
                                                </p>
                                            ))
                                        ) : (
                                            <p className="text-sm text-foreground">No immediate action</p>
                                        )}
                                    </div>
                                </div>
                            </div>

                            {dimension.status === "SAFE" && dimension.interpretation && (
                                <div className="rounded-xl border border-emerald-500/15 bg-emerald-500/8 px-4 py-3 text-sm text-emerald-50/90">
                                    {dimension.interpretation}
                                </div>
                            )}

                            {hasBreakdown && (
                                <div>
                                    <h4 className="mb-4 text-xs font-mono font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                                        Risk Contribution
                                    </h4>
                                    <RiskBreakdownChart
                                        dominant={dimension.breakdown.dominant}
                                        additive={dimension.breakdown.additive}
                                    />
                                </div>
                            )}

                            {previewSignals.length > 0 && (
                                <div>
                                    <h4 className="mb-3 text-xs font-mono font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                                        Most Relevant Signals
                                    </h4>
                                    <div className="space-y-2">
                                        {previewSignals.map((signal) => (
                                            <div
                                                key={`${signal.label}-${signal.value}`}
                                                className="flex items-center justify-between rounded-xl border border-white/8 bg-white/[0.02] px-3 py-2.5"
                                            >
                                                <span className="text-sm text-muted-foreground">
                                                    {signal.label}
                                                </span>
                                                <span className="text-sm font-mono text-foreground">
                                                    {signal.value}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {hasSignalDetails && (
                                <details className="rounded-xl border border-white/8 bg-white/[0.02]">
                                    <summary className="cursor-pointer list-none px-4 py-3 text-sm font-medium text-foreground">
                                        View All Signals
                                    </summary>
                                    <div className="border-t border-white/[0.06] p-3">
                                        <SignalTable signals={dimension.signals} />
                                    </div>
                                </details>
                            )}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
