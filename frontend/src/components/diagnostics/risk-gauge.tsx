"use client";

import clsx from "clsx";

interface RiskGaugeProps {
    risk: number;       // 0–1
    status: string;     // "SAFE" | "WARNING" | "CRITICAL"
    className?: string;
}

function getStatusColor(status: string) {
    const s = status.toUpperCase();
    if (s === "CRITICAL") return {
        text: "text-red-400",
        glow: "shadow-red-500/20",
        stroke: "#ef4444",
        bg: "bg-red-500/10",
        border: "border-red-500/25",
        label: "CRITICAL",
    };
    if (s === "WARNING") return {
        text: "text-amber-400",
        glow: "shadow-amber-500/20",
        stroke: "#f59e0b",
        bg: "bg-amber-500/10",
        border: "border-amber-500/25",
        label: "WARNING",
    };
    return {
        text: "text-emerald-400",
        glow: "shadow-emerald-500/20",
        stroke: "#10b981",
        bg: "bg-emerald-500/10",
        border: "border-emerald-500/25",
        label: "SAFE",
    };
}

function getInterpretation(risk: number, status: string): string {
    const s = status.toUpperCase();
    if (s === "SAFE") return "All structural dimensions are within acceptable thresholds.";
    if (s === "WARNING") return "Moderate structural risk detected. Some dimensions need attention before modeling.";
    return "Severe structural issues detected. Data is not reliable for modeling in its current state.";
}

export function RiskGauge({ risk, status, className }: RiskGaugeProps) {
    const colors = getStatusColor(status);
    const clampedRisk = Math.max(0, Math.min(1, risk));

    // SVG arc parameters
    const size = 200;
    const strokeWidth = 12;
    const radius = (size - strokeWidth) / 2;
    const circumference = Math.PI * radius; // semi-circle
    const arcOffset = circumference * (1 - clampedRisk);

    return (
        <div className={clsx("flex flex-col items-center", className)}>
            {/* Arc gauge */}
            <div className="relative" style={{ width: size, height: size / 2 + 30 }}>
                <svg
                    width={size}
                    height={size / 2 + strokeWidth}
                    viewBox={`0 0 ${size} ${size / 2 + strokeWidth}`}
                    className="overflow-visible"
                >
                    {/* Background arc */}
                    <path
                        d={`M ${strokeWidth / 2} ${size / 2} A ${radius} ${radius} 0 0 1 ${size - strokeWidth / 2} ${size / 2}`}
                        fill="none"
                        stroke="rgba(255,255,255,0.06)"
                        strokeWidth={strokeWidth}
                        strokeLinecap="round"
                    />
                    {/* Filled arc */}
                    <path
                        d={`M ${strokeWidth / 2} ${size / 2} A ${radius} ${radius} 0 0 1 ${size - strokeWidth / 2} ${size / 2}`}
                        fill="none"
                        stroke={colors.stroke}
                        strokeWidth={strokeWidth}
                        strokeLinecap="round"
                        strokeDasharray={circumference}
                        strokeDashoffset={arcOffset}
                        className="transition-all duration-1000 ease-out"
                        style={{ filter: `drop-shadow(0 0 8px ${colors.stroke}40)` }}
                    />
                </svg>

                {/* Center content */}
                <div className="absolute inset-0 flex flex-col items-center justify-end pb-2">
                    <span
                        className={clsx(
                            "text-4xl md:text-5xl font-bold tabular-nums tracking-tight",
                            colors.text
                        )}
                    >
                        {clampedRisk.toFixed(2)}
                    </span>
                </div>
            </div>

            {/* Status label */}
            <div
                className={clsx(
                    "inline-flex items-center gap-2 px-4 py-1.5 rounded-full border mt-2",
                    colors.bg,
                    colors.border
                )}
            >
                <span className="relative flex h-2 w-2">
                    <span
                        className={clsx(
                            "animate-ping absolute inline-flex h-full w-full rounded-full opacity-75",
                            status.toUpperCase() === "SAFE" ? "bg-emerald-500" :
                            status.toUpperCase() === "WARNING" ? "bg-amber-500" : "bg-red-500"
                        )}
                    />
                    <span
                        className={clsx(
                            "relative inline-flex rounded-full h-2 w-2",
                            status.toUpperCase() === "SAFE" ? "bg-emerald-500" :
                            status.toUpperCase() === "WARNING" ? "bg-amber-500" : "bg-red-500"
                        )}
                    />
                </span>
                <span
                    className={clsx(
                        "text-xs font-mono font-semibold uppercase tracking-widest",
                        colors.text
                    )}
                >
                    {colors.label}
                </span>
            </div>

            {/* Interpretation */}
            <p className="text-sm font-mono text-muted-foreground/70 text-center max-w-md mt-4 leading-relaxed">
                {getInterpretation(clampedRisk, status)}
            </p>
        </div>
    );
}
