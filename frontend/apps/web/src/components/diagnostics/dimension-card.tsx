"use client";

import { useState } from "react";
import clsx from "clsx";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Shield, Database, Target, BarChart3 } from "lucide-react";
import type { DimensionResult } from "@/lib/api";
import { RiskBar } from "./risk-bar";
import { RiskBreakdownChart } from "./risk-breakdown-chart";
import { SignalTable } from "./signal-table";
import {
    Tooltip,
    TooltipContent,
    TooltipTrigger,
} from "@/components/ui/tooltip";

interface DimensionCardProps {
    name: string;           // e.g. "data_integrity"
    dimension: DimensionResult;
    defaultExpanded?: boolean;
    className?: string;
}

const DIMENSION_META: Record<string, {
    label: string;
    description: string;
    icon: typeof Shield;
}> = {
    data_integrity: {
        label: "Data Integrity",
        description: "Structural completeness and consistency of the raw data — missing values, duplicates, type ambiguity, and hidden corruption.",
        icon: Shield,
    },
    target_viability: {
        label: "Target Viability",
        description: "Quality and usability of the target variable — class balance, missing targets, type consistency, and learnability.",
        icon: Target,
    },
    sample_adequacy: {
        label: "Sample Adequacy",
        description: "Whether the dataset has sufficient samples relative to its feature space to support reliable model training.",
        icon: BarChart3,
    },
};

function getStatusStyles(status: string) {
    const s = status.toUpperCase();
    if (s === "CRITICAL") return {
        bg: "bg-red-500/10",
        border: "border-red-500/20",
        borderHover: "hover:border-red-500/35",
        text: "text-red-400",
        dot: "bg-red-500",
        badge: "bg-red-500/15 text-red-400 border-red-500/25",
    };
    if (s === "WARNING") return {
        bg: "bg-amber-500/10",
        border: "border-amber-500/20",
        borderHover: "hover:border-amber-500/35",
        text: "text-amber-400",
        dot: "bg-amber-500",
        badge: "bg-amber-500/15 text-amber-400 border-amber-500/25",
    };
    return {
        bg: "bg-emerald-500/10",
        border: "border-emerald-500/20",
        borderHover: "hover:border-emerald-500/35",
        text: "text-emerald-400",
        dot: "bg-emerald-500",
        badge: "bg-emerald-500/15 text-emerald-400 border-emerald-500/25",
    };
}

export function DimensionCard({
    name,
    dimension,
    defaultExpanded = false,
    className,
}: DimensionCardProps) {
    const [expanded, setExpanded] = useState(defaultExpanded);
    const meta = DIMENSION_META[name] ?? {
        label: name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
        description: "",
        icon: Database,
    };
    const styles = getStatusStyles(dimension.status);
    const Icon = meta.icon;

    const hasDominant = Object.keys(dimension.breakdown.dominant).length > 0;
    const hasAdditive = Object.keys(dimension.breakdown.additive).length > 0;
    const hasBreakdown = hasDominant || hasAdditive;

    return (
        <div
                className={clsx(
                    "rounded-xl border backdrop-blur transition-all duration-300",
                    styles.border,
                    styles.borderHover,
                    "bg-card/60",
                    expanded && styles.bg,
                    className
                )}
            >
                {/* ── Header ── */}
                <div
                    role="button"
                    tabIndex={0}
                    onClick={() => setExpanded(!expanded)}
                    onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); setExpanded(!expanded); } }}
                    className="w-full flex items-center gap-4 p-5 md:p-6 text-left cursor-pointer group"
                >
                    {/* Icon */}
                    <div
                        className={clsx(
                            "size-10 rounded-lg flex items-center justify-center shrink-0 transition-colors",
                            styles.bg
                        )}
                    >
                        <Icon className={clsx("size-5", styles.text)} />
                    </div>

                    {/* Label + Description */}
                    <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2.5">
                            <h3 className="text-base font-semibold tracking-tight truncate">
                                {meta.label}
                            </h3>
                            {/* Status badge */}
                            <span
                                className={clsx(
                                    "inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold uppercase tracking-widest border",
                                    styles.badge
                                )}
                            >
                                <span className={clsx("size-1.5 rounded-full", styles.dot)} />
                                {dimension.status.toUpperCase()}
                            </span>
                        </div>
                        {/* Mini risk bar */}
                        <div className="mt-2.5 max-w-48">
                            <RiskBar risk={dimension.risk} height="h-1.5" showMarker={false} />
                        </div>
                    </div>

                    {/* Risk score */}
                    <Tooltip>
                        <TooltipTrigger
                            className={clsx(
                                "text-2xl md:text-3xl font-bold tabular-nums tracking-tight shrink-0",
                                styles.text
                            )}
                        >
                            {dimension.risk.toFixed(2)}
                        </TooltipTrigger>
                        <TooltipContent side="left" className="text-xs max-w-48">
                            <p className="font-medium">Risk Score</p>
                            <p className="text-muted-foreground mt-0.5">
                                0.00 = no risk, 1.00 = maximum risk. Computed from dominant and additive risk factors.
                            </p>
                        </TooltipContent>
                    </Tooltip>

                    {/* Chevron */}
                    <ChevronDown
                        className={clsx(
                            "size-5 text-muted-foreground transition-transform duration-300 shrink-0",
                            expanded && "rotate-180"
                        )}
                    />
                </div>

                {/* ── Expanded Content ── */}
                <AnimatePresence initial={false}>
                    {expanded && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.3, ease: "easeInOut" }}
                            className="overflow-hidden"
                        >
                            <div className="px-5 md:px-6 pb-6 space-y-6">
                                {/* Separator */}
                                <div className="border-t border-white/[0.06]" />

                                {/* Dimension description */}
                                {meta.description && (
                                    <p className="text-sm font-mono text-muted-foreground/60 leading-relaxed">
                                        {meta.description}
                                    </p>
                                )}

                                {/* Risk Breakdown */}
                                {hasBreakdown && (
                                    <div>
                                        <h4 className="text-xs font-mono font-semibold uppercase tracking-widest text-muted-foreground mb-4">
                                            Risk Breakdown — Why this risk exists
                                        </h4>

                                        <RiskBreakdownChart
                                            dominant={dimension.breakdown.dominant}
                                            additive={dimension.breakdown.additive}
                                        />

                                        {/* Dominant risks callout */}
                                        {hasDominant && (
                                            <div className="mt-4 p-3 rounded-lg bg-amber-500/5 border border-amber-500/10">
                                                <p className="text-[10px] font-mono uppercase tracking-widest text-amber-400/80 mb-2">
                                                    Dominant Risks (non-dilutable)
                                                </p>
                                                <div className="space-y-1">
                                                    {Object.entries(dimension.breakdown.dominant).map(([key, val]) => (
                                                        <div key={key} className="flex justify-between text-sm font-mono">
                                                            <span className="text-amber-300/80 font-medium">
                                                                {key.replace(/_/g, " ")}
                                                            </span>
                                                            <span className="text-amber-400 font-bold tabular-nums">
                                                                {val.toFixed(3)}
                                                            </span>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {/* Additive risks */}
                                        {hasAdditive && (
                                            <div className="mt-3 p-3 rounded-lg bg-indigo-500/5 border border-indigo-500/10">
                                                <p className="text-[10px] font-mono uppercase tracking-widest text-indigo-400/80 mb-2">
                                                    Additive Risks (combinable)
                                                </p>
                                                <div className="space-y-1">
                                                    {Object.entries(dimension.breakdown.additive).map(([key, val]) => (
                                                        <div key={key} className="flex justify-between text-sm font-mono">
                                                            <span className="text-indigo-300/70">
                                                                {key.replace(/_/g, " ")}
                                                            </span>
                                                            <span className="text-indigo-400 font-medium tabular-nums">
                                                                {val.toFixed(3)}
                                                            </span>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* Signals */}
                                {dimension.signals && Object.keys(dimension.signals).length > 0 && (
                                    <div>
                                        <h4 className="text-xs font-mono font-semibold uppercase tracking-widest text-muted-foreground mb-3">
                                            Raw Signals
                                        </h4>
                                        <div className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-1">
                                            <SignalTable signals={dimension.signals} />
                                        </div>
                                    </div>
                                )}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
        </div>
    );
}
