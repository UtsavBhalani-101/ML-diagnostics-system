"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type { Route } from "next";
import { Activity, AlertTriangle, ShieldCheck, ShieldAlert, ChevronDown, Database, HardDrive, BarChart3 } from "lucide-react";
import type { Layer1FinalOutput, Layer1RiskItem } from "@/lib/api";
import { getLayer1Output } from "@/lib/api";

type PageState = "loading" | "empty" | "ready" | "error";

export default function Layer1ReportPage() {
    const [pageState, setPageState] = useState<PageState>("loading");
    const [data, setData] = useState<Layer1FinalOutput | null>(null);
    const [passedOpen, setPassedOpen] = useState(false);

    useEffect(() => {
        async function fetchData() {
            try {
                const response = await getLayer1Output();
                const output = response?.final_output;
                if (!output || !output.overall_status) {
                    setPageState("empty");
                    return;
                }
                setData(output);
                setPageState("ready");
            } catch {
                setPageState("empty");
            }
        }
        fetchData();
    }, []);

    // ── Loading ──
    if (pageState === "loading") {
        return (
            <main className="flex-grow flex items-center justify-center min-h-[calc(100vh-8rem)]">
                <div className="absolute inset-0 bg-grid-pattern pointer-events-none z-0" />
                <div className="relative z-10 flex flex-col items-center gap-4">
                    <div className="size-12 rounded-full border-2 border-primary/30 border-t-primary animate-spin" />
                    <p className="text-muted-foreground font-mono text-sm tracking-wide">
                        Loading Layer 1 Diagnostics Report…
                    </p>
                </div>
            </main>
        );
    }

    // ── Empty / Error ──
    if (pageState === "empty" || !data) {
        return (
            <main className="flex-grow flex items-center justify-center min-h-[calc(100vh-8rem)]">
                <div className="absolute inset-0 bg-grid-pattern pointer-events-none z-0" />
                <div className="relative z-10 flex flex-col items-center gap-6 text-center px-6">
                    <div className="size-16 rounded-full bg-white/5 border border-white/10 flex items-center justify-center">
                        <Activity className="size-8 text-muted-foreground" />
                    </div>
                    <div>
                        <h2 className="text-xl font-semibold mb-2">No diagnostics report available.</h2>
                        <p className="text-muted-foreground font-mono text-sm">
                            Please run Layer 1 analysis first.
                        </p>
                    </div>
                    <Link
                        href={"/diagnostics" as Route}
                        className="inline-flex items-center gap-2 px-6 py-2.5 rounded-lg bg-primary text-white text-sm font-medium hover:bg-primary/90 transition-colors"
                    >
                        ← Back to Diagnostics
                    </Link>
                </div>
            </main>
        );
    }

    // ── Helpers ──
    const statusColor = (s: string) => {
        const v = s.toUpperCase();
        if (v === "CRITICAL" || v === "DANGER") return { bg: "bg-red-500/10", border: "border-red-500/30", text: "text-red-400", dot: "bg-red-500" };
        if (v === "WARNING") return { bg: "bg-amber-500/10", border: "border-amber-500/30", text: "text-amber-400", dot: "bg-amber-500" };
        return { bg: "bg-emerald-500/10", border: "border-emerald-500/30", text: "text-emerald-400", dot: "bg-emerald-500" };
    };

    const overall = statusColor(data.overall_status);
    const summary = data.summary;
    const facts = data.key_facts;
    const criticalRisks = data.risks?.critical ?? [];
    const warningRisks = data.risks?.warning ?? [];
    const noIssues = data.no_issues ?? [];

    const safe = (v: unknown, fallback: string = "N/A") =>
        v !== null && v !== undefined && v !== "" ? String(v) : fallback;

    return (
        <main className="flex-grow flex flex-col relative min-h-[calc(100vh-8rem)]">
            <div className="absolute inset-0 bg-grid-pattern pointer-events-none z-0" />

            <section className="relative z-10 w-full max-w-6xl mx-auto py-12 px-6 flex flex-col gap-8">
                {/* ── Page Header ── */}
                <div className="flex items-center gap-3 mb-2">
                    <Link href={"/diagnostics" as Route} className="text-muted-foreground hover:text-foreground transition-colors text-sm font-mono">
                        ← Diagnostics
                    </Link>
                    <span className="text-muted-foreground/40">/</span>
                    <span className="text-sm font-mono text-foreground">Layer 1 Report</span>
                </div>

                {/* ── Layer Context Tag ── */}
                <div className="mb-1">
                    <p className="text-sm font-semibold font-mono tracking-wide text-muted-foreground">
                        Layer 1 — Global Structural Validation
                    </p>
                    <p className="text-xs font-mono text-muted-foreground/75 mt-0.5">
                        Pre-model structural integrity assessment.
                    </p>
                </div>

                {/* ══════ 1. Overall Status Banner ══════ */}
                <div className={`rounded-xl border ${overall.border} ${overall.bg} p-6 flex items-center gap-5`}>
                    <div className={`size-14 rounded-full ${overall.bg} border ${overall.border} flex items-center justify-center shrink-0`}>
                        {data.overall_status.toUpperCase() === "SAFE" ? (
                            <ShieldCheck className={`size-7 ${overall.text}`} />
                        ) : (
                            <ShieldAlert className={`size-7 ${overall.text}`} />
                        )}
                    </div>
                    <div>
                        <p className="text-xs font-mono uppercase tracking-widest text-muted-foreground mb-1">
                            Overall Data Risk
                        </p>
                        <h2 className={`text-2xl md:text-3xl font-bold tracking-tight ${overall.text}`}>
                            {data.overall_status.toUpperCase()}
                        </h2>
                    </div>
                    <div className={`ml-auto size-3 rounded-full ${overall.dot} animate-pulse`} />
                </div>

                {/* ══════ 2. Summary Cards ══════ */}
                {summary && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <SummaryCard label="Total Tests" value={safe(summary.total_tests)} accent="text-primary" />
                        <SummaryCard label="Critical" value={safe(summary.critical)} accent="text-red-400" />
                        <SummaryCard label="Warning" value={safe(summary.warning)} accent="text-amber-400" />
                        <SummaryCard label="Safe" value={safe(summary.safe)} accent="text-emerald-400" />
                    </div>
                )}

                {/* ══════ 3. Key Facts ══════ */}
                {facts && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {/* Dataset Size */}
                        {facts.size && (
                            <div className="rounded-xl border border-border bg-card/60 backdrop-blur p-5">
                                <div className="flex items-center gap-2 mb-4">
                                    <Database className="size-4 text-primary" />
                                    <h3 className="text-sm font-semibold uppercase tracking-wide">Dataset Size</h3>
                                </div>
                                <div className="space-y-2 text-sm font-mono">
                                    <Fact label="Rows" value={safe(facts.size.rows?.toLocaleString())} />
                                    <Fact label="Columns" value={safe(facts.size.columns)} />
                                    <Fact label="Scale" value={safe(facts.size.scale)} />
                                </div>
                            </div>
                        )}
                        {/* Memory */}
                        {facts.memory && (
                            <div className="rounded-xl border border-border bg-card/60 backdrop-blur p-5">
                                <div className="flex items-center gap-2 mb-4">
                                    <HardDrive className="size-4 text-primary" />
                                    <h3 className="text-sm font-semibold uppercase tracking-wide">Memory</h3>
                                </div>
                                <div className="space-y-2 text-sm font-mono">
                                    <Fact label="Usage" value={facts.memory.usage_mb != null ? `${facts.memory.usage_mb} MB` : "N/A"} />
                                    <Fact label="Class" value={safe(facts.memory.class)} />
                                </div>
                            </div>
                        )}
                        {/* Feature Mix */}
                        {facts.feature_mix && (
                            <div className="rounded-xl border border-border bg-card/60 backdrop-blur p-5">
                                <div className="flex items-center gap-2 mb-4">
                                    <BarChart3 className="size-4 text-primary" />
                                    <h3 className="text-sm font-semibold uppercase tracking-wide">Feature Mix</h3>
                                </div>
                                <div className="space-y-2 text-sm font-mono">
                                    <Fact label="Type" value={safe(facts.feature_mix.type)} />
                                    <Fact label="Numeric" value={facts.feature_mix.numeric_ratio != null ? `${(facts.feature_mix.numeric_ratio * 100).toFixed(0)}%` : "N/A"} />
                                    <Fact label="Categorical" value={facts.feature_mix.categorical_ratio != null ? `${(facts.feature_mix.categorical_ratio * 100).toFixed(0)}%` : "N/A"} />
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* ══════ 4. Critical Risks ══════ */}
                {criticalRisks.length > 0 && (
                    <div>
                        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <ShieldAlert className="size-5 text-red-400" />
                            Critical Risks
                            <span className="text-xs font-mono bg-red-500/15 text-red-400 px-2 py-0.5 rounded-full ml-1">{criticalRisks.length}</span>
                        </h3>
                        <div className="grid gap-4">
                            {criticalRisks.map((risk, i) => (
                                <RiskCard key={risk.id ?? i} risk={risk} severity="critical" />
                            ))}
                        </div>
                    </div>
                )}

                {/* ══════ 5. Warning Risks ══════ */}
                {warningRisks.length > 0 && (
                    <div>
                        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <AlertTriangle className="size-5 text-amber-400" />
                            Warning Risks
                            <span className="text-xs font-mono bg-amber-500/15 text-amber-400 px-2 py-0.5 rounded-full ml-1">{warningRisks.length}</span>
                        </h3>
                        <div className="grid gap-4">
                            {warningRisks.map((risk, i) => (
                                <RiskCard key={risk.id ?? i} risk={risk} severity="warning" />
                            ))}
                        </div>
                    </div>
                )}

                {/* ══════ 6. Passed Checks (Collapsible) ══════ */}
                {noIssues.length > 0 && (
                    <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 overflow-hidden">
                        <button
                            onClick={() => setPassedOpen(!passedOpen)}
                            className="w-full flex items-center justify-between px-6 py-4 text-left hover:bg-emerald-500/5 transition-colors cursor-pointer"
                        >
                            <span className="flex items-center gap-2 text-sm font-semibold">
                                <ShieldCheck className="size-4 text-emerald-400" />
                                Passed Checks ({noIssues.length})
                            </span>
                            <ChevronDown className={`size-4 text-emerald-400 transition-transform duration-200 ${passedOpen ? "rotate-180" : ""}`} />
                        </button>
                        {passedOpen && (
                            <div className="px-6 pb-4 space-y-3">
                                {noIssues.map((item, i) => (
                                    <div key={item.id ?? i} className="flex items-start gap-3 py-2 border-t border-emerald-500/10 first:border-0">
                                        <div className="size-2 rounded-full bg-emerald-500 mt-1.5 shrink-0" />
                                        <div>
                                            <p className="text-sm font-medium">{safe(item.check_name)}</p>
                                            <p className="text-xs text-muted-foreground font-mono mt-0.5">{safe(item.title)}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* Bottom spacer */}
                <div className="h-8" />
            </section>
        </main>
    );
}

/* ──────────────────── Sub-components ──────────────────── */

function SummaryCard({ label, value, accent }: { label: string; value: string; accent: string }) {
    return (
        <div className="rounded-xl border border-border bg-card/60 backdrop-blur p-5 text-center">
            <p className={`text-3xl font-bold ${accent}`}>{value}</p>
            <p className="text-xs font-mono uppercase tracking-wide text-muted-foreground mt-1">{label}</p>
        </div>
    );
}

function Fact({ label, value }: { label: string; value: string }) {
    return (
        <div className="flex justify-between items-center">
            <span className="text-muted-foreground">{label}</span>
            <span className="font-medium text-foreground">{value}</span>
        </div>
    );
}

function RiskCard({ risk, severity }: { risk: Layer1RiskItem; severity: "critical" | "warning" }) {
    const isCritical = severity === "critical";
    const borderColor = isCritical ? "border-red-500/25" : "border-amber-500/25";
    const bgColor = isCritical ? "bg-red-500/5" : "bg-amber-500/5";
    const accentText = isCritical ? "text-red-400" : "text-amber-400";
    const badgeBg = isCritical ? "bg-red-500/15" : "bg-amber-500/15";

    const safe = (v: unknown, fb: string = "N/A") =>
        v !== null && v !== undefined && v !== "" ? String(v) : fb;

    return (
        <div className={`rounded-xl border ${borderColor} ${bgColor} p-5`}>
            <div className="flex items-start justify-between gap-4 mb-3">
                <div className="flex-1 min-w-0">
                    <h4 className="font-semibold text-sm">{safe(risk.title)}</h4>
                    <p className="text-xs text-muted-foreground font-mono mt-1">{safe(risk.check_name)}</p>
                </div>
                <span className={`text-xs font-mono px-2 py-0.5 rounded-full shrink-0 ${badgeBg} ${accentText}`}>
                    {safe(risk.scope)}
                </span>
            </div>

            <div className="flex flex-wrap gap-4 text-xs font-mono text-muted-foreground">
                <span>Metric: <span className={`font-medium ${accentText}`}>{safe(risk.metric)}</span></span>
                {risk.risk_code && <span>Code: {risk.risk_code}</span>}
            </div>

            {/* Details from info */}
            {typeof risk.info?.details === "string" ? (
                <p className="mt-3 text-xs text-muted-foreground border-t border-white/5 pt-3">
                    {risk.info.details}
                </p>
            ) : null}

            {/* Affected columns */}
            {risk.columns && risk.columns.length > 0 && (
                <div className="mt-3 border-t border-white/5 pt-3">
                    <p className="text-xs text-muted-foreground mb-1.5">Affected Columns:</p>
                    <div className="flex flex-wrap gap-1.5">
                        {risk.columns.map((col) => (
                            <span key={col} className={`text-xs font-mono px-2 py-0.5 rounded ${badgeBg} ${accentText}`}>
                                {col}
                            </span>
                        ))}
                    </div>
                </div>
            )}

            {/* Detected placeholders */}
            {risk.detected_placeholders && risk.detected_placeholders.length > 0 && (
                <div className="mt-3 border-t border-white/5 pt-3">
                    <p className="text-xs text-muted-foreground mb-1.5">Detected Placeholders:</p>
                    <div className="flex flex-wrap gap-1.5">
                        {risk.detected_placeholders.map((ph) => (
                            <span key={ph} className={`text-xs font-mono px-2 py-0.5 rounded ${badgeBg} ${accentText}`}>
                                {`"${ph}"`}
                            </span>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
