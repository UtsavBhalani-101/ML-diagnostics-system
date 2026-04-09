"use client";

import clsx from "clsx";

interface RiskBarProps {
    risk: number;       // 0–1
    height?: string;    // tailwind height class
    showMarker?: boolean;
    showLabels?: boolean;
    className?: string;
}

function getBarGradient(risk: number): string {
    if (risk < 0.3) return "from-emerald-500/80 to-emerald-400/60";
    if (risk < 0.7) return "from-amber-500/80 to-amber-400/60";
    return "from-red-500/80 to-red-400/60";
}

function getMarkerColor(risk: number): string {
    if (risk < 0.3) return "bg-emerald-400 shadow-emerald-400/50";
    if (risk < 0.7) return "bg-amber-400 shadow-amber-400/50";
    return "bg-red-400 shadow-red-400/50";
}

export function RiskBar({
    risk,
    height = "h-2",
    showMarker = true,
    showLabels = false,
    className,
}: RiskBarProps) {
    const clampedRisk = Math.max(0, Math.min(1, risk));
    const percentage = clampedRisk * 100;

    return (
        <div className={clsx("w-full", className)}>
            {/* Labels */}
            {showLabels && (
                <div className="flex justify-between mb-1.5">
                    <span className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">
                        0.0
                    </span>
                    <span className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">
                        1.0
                    </span>
                </div>
            )}

            {/* Track */}
            <div
                className={clsx(
                    "relative w-full rounded-full overflow-hidden",
                    height,
                    "bg-white/[0.06]"
                )}
            >
                {/* Fill */}
                <div
                    className={clsx(
                        "absolute inset-y-0 left-0 rounded-full bg-gradient-to-r transition-all duration-700 ease-out",
                        getBarGradient(clampedRisk)
                    )}
                    style={{ width: `${percentage}%` }}
                />

                {/* Marker */}
                {showMarker && (
                    <div
                        className="absolute top-1/2 -translate-y-1/2 transition-all duration-700 ease-out"
                        style={{ left: `${percentage}%` }}
                    >
                        <div
                            className={clsx(
                                "size-3 -ml-1.5 rounded-full shadow-lg",
                                getMarkerColor(clampedRisk)
                            )}
                        />
                    </div>
                )}
            </div>
        </div>
    );
}
