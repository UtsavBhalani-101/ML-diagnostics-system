"use client";

import clsx from "clsx";
import {
    Tooltip,
    TooltipContent,
    TooltipTrigger,
} from "@/components/ui/tooltip";
import { Info } from "lucide-react";

interface SignalTableProps {
    signals: Record<string, unknown>;
    className?: string;
}

// Human-readable labels for known signal keys
const SIGNAL_LABELS: Record<string, { label: string; description: string }> = {
    rows: { label: "Rows", description: "Total number of rows in the dataset" },
    cols: { label: "Columns", description: "Total number of columns" },
    global_missing_ratio: { label: "Global Missing", description: "Fraction of all cells that are missing (NaN/null)" },
    column_missing_ratio: { label: "Column Missing", description: "Per-column missing value ratios" },
    duplicate_ratio: { label: "Duplicates", description: "Fraction of rows that are exact duplicates" },
    constant_columns: { label: "Constant Cols", description: "Columns with zero variance (single unique value)" },
    constant_ratio: { label: "Constant Ratio", description: "Fraction of features that are constant" },
    hidden_missing_ratio: { label: "Hidden Missing", description: "Placeholder values masquerading as real data (e.g. '?', '-', 'N/A')" },
    mixed_type_columns: { label: "Mixed Types", description: "Columns containing multiple data types" },
    mixed_ratio: { label: "Mixed Ratio", description: "Fraction of columns with mixed data types" },
    class_balance_ratio: { label: "Class Balance", description: "Ratio of minority to majority class" },
    n_classes: { label: "# Classes", description: "Number of unique target classes" },
    target_missing_ratio: { label: "Target Missing", description: "Fraction of missing values in the target column" },
    target_type: { label: "Target Type", description: "Detected data type of the target column" },
    target_unique_ratio: { label: "Target Unique", description: "Ratio of unique values in target" },
    sample_feature_ratio: { label: "Sample/Feature", description: "Ratio of samples to features — higher is better" },
};

function formatValue(value: unknown): string {
    if (value === null || value === undefined) return "—";
    if (typeof value === "number") {
        if (Number.isInteger(value)) return value.toLocaleString();
        if (Math.abs(value) < 0.001 && value !== 0) return value.toExponential(2);
        return value.toFixed(4);
    }
    if (typeof value === "boolean") return value ? "Yes" : "No";
    if (Array.isArray(value)) {
        if (value.length === 0) return "None";
        return value.join(", ");
    }
    if (typeof value === "object") return JSON.stringify(value);
    return String(value);
}

function isNestedObject(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function SignalTable({ signals, className }: SignalTableProps) {
    // Separate flat values from nested objects
    const flatEntries: [string, unknown][] = [];
    const nestedEntries: [string, Record<string, unknown>][] = [];

    for (const [key, value] of Object.entries(signals)) {
        if (isNestedObject(value)) {
            nestedEntries.push([key, value]);
        } else {
            flatEntries.push([key, value]);
        }
    }

    return (
            <div className={clsx("space-y-0.5", className)}>
                {/* Flat signal values */}
                {flatEntries.map(([key, value]) => {
                    const meta = SIGNAL_LABELS[key];
                    return (
                        <div
                            key={key}
                            className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-white/[0.03] transition-colors group"
                        >
                            <div className="flex items-center gap-2 min-w-0">
                                <span className="text-sm font-mono text-muted-foreground truncate">
                                    {meta?.label ?? key}
                                </span>
                                {meta?.description && (
                                    <Tooltip>
                                        <TooltipTrigger>
                                            <Info className="size-3 text-muted-foreground/50 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity cursor-help" />
                                        </TooltipTrigger>
                                        <TooltipContent
                                            side="right"
                                            className="max-w-64 text-xs"
                                        >
                                            {meta.description}
                                        </TooltipContent>
                                    </Tooltip>
                                )}
                            </div>
                            <span className="text-sm font-mono font-medium text-foreground tabular-nums ml-4">
                                {formatValue(value)}
                            </span>
                        </div>
                    );
                })}

                {/* Nested signal objects (e.g. column_missing_ratio) */}
                {nestedEntries.map(([key, obj]) => {
                    const meta = SIGNAL_LABELS[key];
                    const entries = Object.entries(obj);
                    if (entries.length === 0) return null;

                    return (
                        <details key={key} className="group/nested">
                            <summary className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-white/[0.03] transition-colors cursor-pointer list-none">
                                <div className="flex items-center gap-2">
                                    <span className="text-sm font-mono text-muted-foreground">
                                        {meta?.label ?? key}
                                    </span>
                                    {meta?.description && (
                                        <Tooltip>
                                            <TooltipTrigger>
                                                <Info className="size-3 text-muted-foreground/50 shrink-0 cursor-help" />
                                            </TooltipTrigger>
                                            <TooltipContent
                                                side="right"
                                                className="max-w-64 text-xs"
                                            >
                                                {meta.description}
                                            </TooltipContent>
                                        </Tooltip>
                                    )}
                                </div>
                                <span className="text-xs font-mono text-muted-foreground/60">
                                    {entries.length} entries ▸
                                </span>
                            </summary>
                            <div className="ml-4 pl-3 border-l border-white/[0.06] mt-1 mb-2">
                                {entries.map(([subKey, subVal]) => (
                                    <div
                                        key={subKey}
                                        className="flex items-center justify-between py-1.5 px-2"
                                    >
                                        <span className="text-xs font-mono text-muted-foreground/80 truncate">
                                            {subKey}
                                        </span>
                                        <span className="text-xs font-mono font-medium text-foreground/80 tabular-nums ml-4">
                                            {formatValue(subVal)}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </details>
                    );
                })}
        </div>
    );
}
