"use client";

import clsx from "clsx";
import { AlertTriangle, CheckCircle2, CircleSlash, Database, Shield, Target } from "lucide-react";
import type { ValidationCheck, ValidationSection, ValidationStatus } from "@/lib/layer1-validation";

interface DimensionCardProps {
    section: ValidationSection;
    className?: string;
}

const STATUS_STYLES: Record<ValidationStatus, {
    label: string;
    badge: string;
    accent: string;
    iconClass: string;
    title: string;
    icon: typeof CheckCircle2;
}> = {
    PASS: {
        label: "PASS",
        badge: "border-border text-foreground",
        accent: "border-l-border",
        iconClass: "text-green-500",
        title: "font-medium",
        icon: CheckCircle2,
    },
    FAIL: {
        label: "FAIL",
        badge: "border-red-500 text-red-500",
        accent: "border-l-red-500",
        iconClass: "text-red-500",
        title: "font-bold",
        icon: CircleSlash,
    },
    WARNING: {
        label: "WARNING",
        badge: "border-amber-500 text-amber-500",
        accent: "border-l-amber-500",
        iconClass: "text-amber-500",
        title: "font-semibold",
        icon: AlertTriangle,
    },
};

const SECTION_ICONS = {
    data_integrity: Shield,
    target_viability: Target,
    sample_adequacy: Database,
};

function countByStatus(checks: ValidationCheck[], status: ValidationStatus): number {
    return checks.filter((check) => check.status === status).length;
}

function StatusBadge({ status }: { status: ValidationStatus }) {
    const styles = STATUS_STYLES[status];
    const Icon = styles.icon;

    return (
        <span
            className={clsx(
                "inline-flex w-fit items-center gap-1.5 rounded-md border px-2 py-1 font-mono text-[10px] font-bold uppercase tracking-widest",
                styles.badge,
            )}
        >
            <Icon className={clsx("size-3", styles.iconClass)} />
            {styles.label}
        </span>
    );
}

function ImpactBadge({ impact }: { impact: ValidationCheck["impact"] }) {
    const className = impact === "BLOCKER"
        ? "border-border text-foreground"
        : "border-border text-muted-foreground";

    return (
        <span className={clsx("inline-flex w-fit rounded-md border px-2 py-1 font-mono text-[10px] font-bold uppercase tracking-widest", className)}>
            {impact}
        </span>
    );
}

function MobileCheckCard({ check }: { check: ValidationCheck }) {
    const styles = STATUS_STYLES[check.status];
    const isPass = check.status === "PASS";

    return (
        <div className={clsx("rounded-md border border-l-4 border-border bg-card p-4", styles.accent, isPass && "py-3")}>
            <div className="mb-3 flex items-start justify-between gap-3">
                <div>
                    <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                        Test
                    </p>
                    <h4 className={clsx("mt-1 text-sm text-foreground", styles.title)}>
                        {check.testName}
                    </h4>
                </div>
                <StatusBadge status={check.status} />
            </div>

            <div className="grid gap-3 font-mono text-xs">
                <MobileField label="Observed" value={check.observed} />
                <MobileField label="Threshold" value={check.threshold} />
                <MobileField label="Rule" value={check.rule} />
                <div>
                    <p className="mb-1 text-[10px] uppercase tracking-widest text-muted-foreground">
                        Impact
                    </p>
                    <ImpactBadge impact={check.impact} />
                </div>
                <MobileField label="Action" value={check.status === "WARNING" && check.optionalAction ? check.optionalAction : check.action} />
            </div>
        </div>
    );
}

function MobileField({ label, value }: { label: string; value: string }) {
    return (
        <div>
            <p className="mb-1 text-[10px] uppercase tracking-widest text-muted-foreground">
                {label}
            </p>
            <p className="text-foreground">{value}</p>
        </div>
    );
}

function CheckRow({ check }: { check: ValidationCheck }) {
    const styles = STATUS_STYLES[check.status];

    return (
        <div
            className={clsx(
                "grid grid-cols-[1.25fr_0.72fr_1fr_1.15fr_1.45fr_0.9fr] gap-3 rounded-md border border-l-4 border-border bg-card px-3 text-sm",
                check.status === "PASS" ? "py-2" : "py-3",
                styles.accent,
            )}
        >
            <div className={clsx("text-foreground", styles.title)}>{check.testName}</div>
            <StatusBadge status={check.status} />
            <div className="font-mono text-xs text-foreground">{check.observed}</div>
            <div className="font-mono text-xs text-muted-foreground">{check.threshold}</div>
            <div className="text-xs leading-relaxed text-foreground">{check.rule}</div>
            <ImpactBadge impact={check.impact} />
        </div>
    );
}

export function DimensionCard({ section, className }: DimensionCardProps) {
    const SectionIcon = SECTION_ICONS[section.key] ?? Database;
    const failCount = countByStatus(section.checks, "FAIL");
    const warningCount = countByStatus(section.checks, "WARNING");
    const passCount = countByStatus(section.checks, "PASS");
    const priorityChecks = section.checks.filter((check) => check.status !== "PASS");
    const passChecks = section.checks.filter((check) => check.status === "PASS");

    return (
        <section className={clsx("rounded-lg border border-border bg-card p-5 md:p-6", className)}>
            <div className="mb-5 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                <div className="flex gap-3">
                    <div className="flex size-10 shrink-0 items-center justify-center rounded-md border border-border bg-background">
                        <SectionIcon className="size-5 text-muted-foreground" />
                    </div>
                    <div>
                        <p className="font-mono text-[10px] font-bold uppercase tracking-[0.2em] text-muted-foreground">
                            Validation Checks
                        </p>
                        <h3 className="mt-1 text-lg font-semibold tracking-tight text-foreground">
                            {section.label}
                        </h3>
                        <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
                            {section.description}
                        </p>
                    </div>
                </div>

                <div className="grid grid-cols-3 gap-2 font-mono text-xs md:min-w-64">
                    <Counter label="FAIL" value={failCount} tone="fail" />
                    <Counter label="WARN" value={warningCount} tone="warning" />
                    <Counter label="PASS" value={passCount} tone="pass" />
                </div>
            </div>

            <div className="hidden md:block">
                <div className="mb-2 grid grid-cols-[1.25fr_0.72fr_1fr_1.15fr_1.45fr_0.9fr] gap-3 px-3 font-mono text-[10px] font-bold uppercase tracking-[0.16em] text-muted-foreground">
                    <span>Test</span>
                    <span>Status</span>
                    <span>Observed</span>
                    <span>Threshold</span>
                    <span>Decision Rule</span>
                    <span>Impact</span>
                </div>
                <div className="space-y-2">
                    {(priorityChecks.length > 0 ? priorityChecks : section.checks).map((check) => (
                        <CheckRow key={check.id} check={check} />
                    ))}
                </div>
                {priorityChecks.length > 0 && passChecks.length > 0 && (
                    <details className="mt-3 rounded-md border border-border bg-background">
                        <summary className="cursor-pointer list-none px-3 py-2 font-mono text-xs text-muted-foreground">
                            {passChecks.length} passing checks collapsed
                        </summary>
                        <div className="space-y-2 border-t border-border p-3">
                            {passChecks.map((check) => (
                                <CheckRow key={check.id} check={check} />
                            ))}
                        </div>
                    </details>
                )}
            </div>

            <div className="space-y-3 md:hidden">
                {(priorityChecks.length > 0 ? priorityChecks : section.checks).map((check) => (
                    <MobileCheckCard key={check.id} check={check} />
                ))}
                {priorityChecks.length > 0 && passChecks.length > 0 && (
                    <details className="rounded-md border border-border bg-background">
                        <summary className="cursor-pointer list-none px-3 py-2 font-mono text-xs text-muted-foreground">
                            {passChecks.length} passing checks collapsed
                        </summary>
                        <div className="space-y-3 border-t border-border p-3">
                            {passChecks.map((check) => (
                                <MobileCheckCard key={check.id} check={check} />
                            ))}
                        </div>
                    </details>
                )}
            </div>
        </section>
    );
}

function Counter({
    label,
    value,
    tone,
}: {
    label: string;
    value: number;
    tone: "fail" | "warning" | "pass";
}) {
    const className = tone === "fail"
        ? "border-l-red-500"
        : tone === "warning"
            ? "border-l-amber-500"
            : "border-l-border";

    return (
        <div className={clsx("rounded-md border border-l-4 border-border bg-background px-3 py-2 text-center text-foreground", className)}>
            <div className="text-lg font-bold tabular-nums">{value}</div>
            <div className="mt-0.5 text-[9px] uppercase tracking-widest text-muted-foreground">{label}</div>
        </div>
    );
}
