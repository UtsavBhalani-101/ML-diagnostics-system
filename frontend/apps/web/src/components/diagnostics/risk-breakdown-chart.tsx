"use client";

import clsx from "clsx";
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    Tooltip as RechartsTooltip,
    ResponsiveContainer,
    Cell,
    Legend,
} from "recharts";

interface RiskBreakdownChartProps {
    dominant: Record<string, number>;
    additive: Record<string, number>;
    className?: string;
}

interface ChartEntry {
    name: string;
    value: number;
    type: "dominant" | "additive";
}

const DOMINANT_COLOR = "#f59e0b";
const ADDITIVE_COLOR = "#6366f1";

function formatLabel(key: string): string {
    return key
        .replace(/_/g, " ")
        .replace(/\b\w/g, (c) => c.toUpperCase());
}

function CustomTooltip({
    active,
    payload,
}: {
    active?: boolean;
    payload?: Array<{ payload: ChartEntry }>;
}) {
    if (!active || !payload || payload.length === 0) return null;
    const data = payload[0]?.payload;
    if (!data) return null;

    return (
        <div className="bg-[#111] border border-white/10 rounded-lg px-3 py-2 shadow-xl">
            <p className="text-xs font-mono text-foreground font-medium">
                {data.name}
            </p>
            <p className="text-xs font-mono text-muted-foreground mt-0.5">
                Risk: <span className="text-foreground font-medium">{data.value.toFixed(3)}</span>
            </p>
            <p className="text-[10px] font-mono mt-0.5" style={{ color: data.type === "dominant" ? DOMINANT_COLOR : ADDITIVE_COLOR }}>
                {data.type === "dominant" ? "▪ Dominant (non-dilutable)" : "▪ Additive (combinable)"}
            </p>
        </div>
    );
}

export function RiskBreakdownChart({
    dominant,
    additive,
    className,
}: RiskBreakdownChartProps) {
    const data: ChartEntry[] = [
        ...Object.entries(dominant).map(([key, value]) => ({
            name: formatLabel(key),
            value,
            type: "dominant" as const,
        })),
        ...Object.entries(additive).map(([key, value]) => ({
            name: formatLabel(key),
            value,
            type: "additive" as const,
        })),
    ];

    // Sort by value descending
    data.sort((a, b) => b.value - a.value);

    if (data.length === 0) {
        return (
            <div className={clsx("text-sm font-mono text-muted-foreground/50 text-center py-4", className)}>
                No risk breakdown data
            </div>
        );
    }

    return (
        <div className={clsx("w-full", className)}>
            <div className="flex items-center gap-4 mb-3">
                <div className="flex items-center gap-1.5">
                    <div className="size-2.5 rounded-sm" style={{ backgroundColor: DOMINANT_COLOR }} />
                    <span className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">
                        Dominant
                    </span>
                </div>
                <div className="flex items-center gap-1.5">
                    <div className="size-2.5 rounded-sm" style={{ backgroundColor: ADDITIVE_COLOR }} />
                    <span className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">
                        Additive
                    </span>
                </div>
            </div>

            <ResponsiveContainer width="100%" height={data.length * 40 + 20}>
                <BarChart
                    data={data}
                    layout="vertical"
                    margin={{ top: 0, right: 10, bottom: 0, left: 0 }}
                    barSize={16}
                >
                    <XAxis
                        type="number"
                        domain={[0, 1]}
                        tick={{ fontSize: 10, fontFamily: "JetBrains Mono", fill: "#64748b" }}
                        tickLine={false}
                        axisLine={{ stroke: "rgba(255,255,255,0.06)" }}
                    />
                    <YAxis
                        type="category"
                        dataKey="name"
                        tick={{ fontSize: 11, fontFamily: "JetBrains Mono", fill: "#94a3b8" }}
                        tickLine={false}
                        axisLine={false}
                        width={90}
                    />
                    <RechartsTooltip
                        content={<CustomTooltip />}
                        cursor={{ fill: "rgba(255,255,255,0.03)" }}
                    />
                    <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                        {data.map((entry, index) => (
                            <Cell
                                key={`cell-${index}`}
                                fill={entry.type === "dominant" ? DOMINANT_COLOR : ADDITIVE_COLOR}
                                fillOpacity={0.8}
                            />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
}
