"use client";

import clsx from "clsx";

interface RiskBreakdownChartProps {
    dominant: Record<string, number>;
    additive: Record<string, number>;
    className?: string;
}

interface Contribution {
    name: string;
    value: number;
    type: "dominant" | "additive";
}

const DOMINANT_COLOR = "linear-gradient(135deg, rgba(245,158,11,0.95), rgba(251,191,36,0.85))";
const ADDITIVE_COLOR = "linear-gradient(135deg, rgba(99,102,241,0.95), rgba(129,140,248,0.8))";

function formatRiskName(key: string): string {
    const labels: Record<string, string> = {
        mixed_types: "Mixed Types",
        hidden_missing: "Hidden Missing",
        missing_values: "Missing Values",
        constant_columns: "Constant Columns",
        low_sample: "Low Sample Support",
        sample_size: "Sample Size",
        task_uncertainty: "Task Uncertainty",
    };

    return labels[key] ?? key.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatRiskValue(value: number): string {
    return value >= 0.01 ? value.toFixed(2) : value.toFixed(3);
}

export function RiskBreakdownChart({
    dominant,
    additive,
    className,
}: RiskBreakdownChartProps) {
    const contributions: Contribution[] = [
        ...Object.entries(dominant).map(([name, value]) => ({
            name,
            value,
            type: "dominant" as const,
        })),
        ...Object.entries(additive).map(([name, value]) => ({
            name,
            value,
            type: "additive" as const,
        })),
    ]
        .filter((item) => item.value > 0)
        .sort((left, right) => right.value - left.value);

    const total = contributions.reduce((sum, item) => sum + item.value, 0);

    if (contributions.length === 0 || total <= 0) {
        return (
            <div className={clsx("rounded-xl border border-white/8 bg-white/[0.02] px-4 py-5 text-sm text-muted-foreground", className)}>
                No material risk contributors in this dimension.
            </div>
        );
    }

    return (
        <div className={clsx("space-y-4", className)}>
            <div className="flex items-center gap-4 text-[10px] font-mono uppercase tracking-[0.18em] text-muted-foreground">
                <div className="flex items-center gap-2">
                    <span className="size-2.5 rounded-full bg-amber-400" />
                    Primary Causes
                </div>
                <div className="flex items-center gap-2">
                    <span className="size-2.5 rounded-full bg-indigo-400" />
                    Contributing Factors
                </div>
            </div>

            <div className="overflow-hidden rounded-2xl border border-white/8 bg-black/20">
                <div className="flex min-h-12 w-full">
                    {contributions.map((item) => {
                        const width = Math.max((item.value / total) * 100, 12);
                        return (
                            <div
                                key={`${item.type}-${item.name}`}
                                className="flex items-center justify-center px-3 py-3 text-center text-[11px] font-mono text-white/90"
                                style={{
                                    width: `${width}%`,
                                    background: item.type === "dominant" ? DOMINANT_COLOR : ADDITIVE_COLOR,
                                }}
                                title={`${formatRiskName(item.name)}: ${formatRiskValue(item.value)}`}
                            >
                                <span className="line-clamp-2">
                                    {formatRiskName(item.name)}
                                </span>
                            </div>
                        );
                    })}
                </div>
            </div>

            <div className="grid gap-2">
                {contributions.map((item) => (
                    <div
                        key={`legend-${item.type}-${item.name}`}
                        className="flex items-center justify-between rounded-xl border border-white/8 bg-white/[0.02] px-3 py-2"
                    >
                        <div className="flex items-center gap-2">
                            <span
                                className="size-2.5 rounded-full"
                                style={{
                                    background: item.type === "dominant" ? "#fbbf24" : "#818cf8",
                                }}
                            />
                            <span className="text-sm text-foreground">
                                {formatRiskName(item.name)}
                            </span>
                        </div>
                        <span className="text-sm font-mono text-muted-foreground">
                            {formatRiskValue(item.value)}
                        </span>
                    </div>
                ))}
            </div>
        </div>
    );
}
