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
    iconClass: string;
    title: string;
    icon: typeof CheckCircle2;
}> = {
    PASS: {
        label: "PASS",
        badge: "border-green-500/35 bg-green-500/10 text-green-400",
        iconClass: "text-green-500",
        title: "font-medium",
        icon: CheckCircle2,
    },
    FAIL: {
        label: "FAIL",
        badge: "border-[#e24b4a]/40 bg-[#e24b4a]/10 text-[#ff7775]",
        iconClass: "text-[#e24b4a]",
        title: "font-bold",
        icon: CircleSlash,
    },
    WARNING: {
        label: "WARNING",
        badge: "border-[#d4901a]/40 bg-[#d4901a]/10 text-[#e9ad43]",
        iconClass: "text-[#d4901a]",
        title: "font-semibold",
        icon: AlertTriangle,
    },
};

const SECTION_ICONS = {
    data_integrity: Shield,
    target_validity: Target,
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
        ? "border-[#e24b4a]/40 bg-[#e24b4a]/10 text-[#ff7775]"
        : impact === "DEGRADING"
            ? "border-[#d4901a]/40 bg-[#d4901a]/10 text-[#e9ad43]"
            : "diag-chip diag-muted";

    return (
        <span className={clsx("inline-flex w-fit rounded border px-2 py-1 font-mono text-[10px] font-bold uppercase tracking-widest", className)}>
            {impact}
        </span>
    );
}

function MobileCheckCard({ check }: { check: ValidationCheck }) {
    const styles = STATUS_STYLES[check.status];
    const isPass = check.status === "PASS";

    return (
        <div className={clsx("diag-row rounded border p-4", isPass && "py-3")}>
            <div className="mb-3 flex items-start justify-between gap-3">
                <div>
                    <p className="diag-muted font-mono text-[10px] uppercase tracking-widest">
                        Test
                    </p>
                    <h4 className={clsx("diag-text mt-1 text-sm", styles.title)}>
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
                    <p className="diag-muted mb-1 text-[10px] uppercase tracking-widest">
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
            <p className="diag-muted mb-1 text-[10px] uppercase tracking-widest">
                {label}
            </p>
            <p className={clsx("diag-text", label === "Threshold" && "diag-muted-soft")}>{value}</p>
        </div>
    );
}

function CheckRow({ check }: { check: ValidationCheck }) {
    const styles = STATUS_STYLES[check.status];

    return (
        <div
            className="diag-row grid grid-cols-[0.72fr_1.2fr_0.95fr_1.15fr_0.86fr] gap-3 rounded border px-3 py-2.5 text-sm transition-colors"
        >
            <StatusBadge status={check.status} />
            <div className={clsx("diag-text", styles.title)}>{check.testName}</div>
            <div className="diag-strong font-mono text-xs">{check.observed}</div>
            <div className="diag-muted-soft font-mono text-xs">{check.threshold}</div>
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
        <section className={clsx("diag-panel rounded-md border p-4 md:p-5", className)}>
            <div className="mb-5 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                <div className="flex gap-3">
                    <div className="diag-body flex size-10 shrink-0 items-center justify-center rounded border [border-color:var(--diag-border)]">
                        <SectionIcon className="diag-muted size-5" />
                    </div>
                    <div>
                        <p className="diag-muted font-mono text-[10px] font-bold uppercase tracking-[0.2em]">
                            Validation Checks
                        </p>
                        <h3 className="diag-strong mt-1 text-lg font-semibold tracking-tight">
                            {section.label}
                        </h3>
                        <p className="diag-muted mt-1 max-w-2xl text-sm">
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
                <div className="diag-muted mb-2 grid grid-cols-[0.72fr_1.2fr_0.95fr_1.15fr_0.86fr] gap-3 px-3 font-mono text-[10px] font-bold uppercase tracking-[0.16em]">
                    <span>Status</span>
                    <span>Test</span>
                    <span>Observed</span>
                    <span className="diag-muted-soft">Threshold</span>
                    <span>Impact</span>
                </div>
                <div className="space-y-2">
                    {(priorityChecks.length > 0 ? priorityChecks : section.checks).map((check) => (
                        <CheckRow key={check.id} check={check} />
                    ))}
                </div>
                {priorityChecks.length > 0 && passChecks.length > 0 && (
                    <details className="diag-row mt-3 rounded border">
                        <summary className="diag-muted cursor-pointer list-none px-3 py-2 font-mono text-xs">
                            {passChecks.length} passing checks collapsed
                        </summary>
                        <div className="space-y-2 border-t p-3 [border-color:var(--diag-border)]">
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
                    <details className="diag-row rounded border">
                        <summary className="diag-muted cursor-pointer list-none px-3 py-2 font-mono text-xs">
                            {passChecks.length} passing checks collapsed
                        </summary>
                        <div className="space-y-3 border-t p-3 [border-color:var(--diag-border)]">
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
        ? "border-[#e24b4a]/40 bg-[#e24b4a]/10 text-[#ff7775]"
        : tone === "warning"
            ? "border-[#d4901a]/40 bg-[#d4901a]/10 text-[#e9ad43]"
            : "border-green-500/30 bg-green-500/10 text-green-400";

    return (
        <div className={clsx("rounded border px-3 py-2 text-center font-mono", className)}>
            <div className="font-sans text-lg font-bold tabular-nums">{value}</div>
            <div className="mt-0.5 text-[9px] uppercase tracking-widest">{label}</div>
        </div>
    );
}
