import type { CheckResult, DimensionResult, Layer1FinalOutput, Layer1KeyFacts } from "@/lib/api";

export type ValidationStatus = "PASS" | "FAIL" | "WARNING";
export type DecisionStatus = "ALLOWED" | "BLOCKED" | "CONDITIONALLY ALLOWED";
export type ImpactLevel = "BLOCKER" | "DEGRADING" | "INFORMATIONAL";

export interface ValidationCheck {
    id: string;
    dimensionKey: string;
    dimensionLabel: string;
    testName: string;
    status: ValidationStatus;
    observed: string;
    threshold: string;
    rule: string;
    impact: ImpactLevel;
    reason: string;
    action: string;
    optionalAction?: string;
    offendingColumns: string[];
}

export interface ValidationSection {
    key: string;
    label: string;
    description: string;
    checks: ValidationCheck[];
}

export interface ValidationDecision {
    status: DecisionStatus;
    tone: "pass" | "fail" | "warning";
    summary: string;
    message: string;
    confidence: "High" | "Medium";
    checksRun: number;
    failureCount: number;
    blockerCount: number;
    warningCount: number;
    degradationCount: number;
}

export interface ValidationModel {
    sections: ValidationSection[];
    checks: ValidationCheck[];
    failures: ValidationCheck[];
    warnings: ValidationCheck[];
    decision: ValidationDecision;
}

// -------------------------
// DIMENSION METADATA
// -------------------------

/** Human-readable labels for known dimension keys. Falls back to the raw key. */
const DIMENSION_LABELS: Record<string, string> = {
    data_integrity: "Data Integrity",
    target_validity: "Target Validity",
    sample_adequacy: "Sample Adequacy",
};

const DIMENSION_DESCRIPTIONS: Record<string, string> = {
    data_integrity: "Structural completeness, dtype consistency, and raw-table trust checks.",
    target_validity: "Target existence, consistency, and learnability checks.",
    sample_adequacy: "Sample support, independence, and feature-space coverage checks.",
};

function dimensionLabel(key: string): string {
    return DIMENSION_LABELS[key] ?? key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function dimensionDescription(key: string): string {
    return DIMENSION_DESCRIPTIONS[key] ?? `Checks for the ${dimensionLabel(key)} dimension.`;
}


// -------------------------
// MAP ENGINE CHECKS → VALIDATION CHECKS
// -------------------------

/**
 * Maps the engine's check label (CRITICAL/WARNING/SAFE/ERROR) to a
 * frontend ValidationStatus (FAIL/WARNING/PASS).
 */
function mapLabelToStatus(label: string | null): ValidationStatus {
    if (!label) return "PASS";
    const upper = label.toUpperCase();
    if (upper === "CRITICAL" || upper === "ERROR" || upper === "STOP") return "FAIL";
    if (upper === "WARNING" || upper === "REVIEW") return "WARNING";
    return "PASS";
}

/**
 * Maps the engine's impact string to the frontend ImpactLevel.
 */
function mapImpact(impact: string | null): ImpactLevel {
    if (!impact) return "INFORMATIONAL";
    const upper = impact.toUpperCase();
    if (upper === "BLOCKER") return "BLOCKER";
    if (upper === "DEGRADING") return "DEGRADING";
    return "INFORMATIONAL";
}

function formatValue(value: unknown): string {
    if (value === null || value === undefined) return "—";
    if (typeof value === "number") {
        if (Number.isInteger(value)) return String(value);
        return value.toFixed(4);
    }
    return String(value);
}

/**
 * Converts a single engine CheckResult into a frontend ValidationCheck.
 * This is the key decoupling point — we take whatever the engine sends
 * and present it, rather than re-deriving from raw signals.
 */
function mapCheck(
    check: CheckResult,
    dimensionKey: string,
    index: number,
): ValidationCheck {
    const status = mapLabelToStatus(check.label);
    const impact = mapImpact(check.impact);

    return {
        id: `${dimensionKey}.${check.name ?? index}`,
        dimensionKey,
        dimensionLabel: dimensionLabel(dimensionKey),
        testName: check.name?.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()) ?? `Check ${index + 1}`,
        status,
        observed: formatValue(check.observed),
        threshold: formatValue(check.threshold),
        rule: `${check.name ?? "check"}: ${check.label ?? "unknown"}`,
        impact,
        reason: check.detail
            ? Object.entries(check.detail)
                .map(([k, v]) => `${k}: ${formatValue(v)}`)
                .join("; ")
            : "No detail provided.",
        action: status === "FAIL"
            ? `Address ${check.name ?? "this issue"} before proceeding.`
            : status === "WARNING"
                ? `Review ${check.name ?? "this signal"} before training.`
                : "No action required.",
        offendingColumns: [],
    };
}


// -------------------------
// BUILD SECTIONS FROM DIMENSIONS
// -------------------------

function buildSection(dimensionKey: string, dimension: DimensionResult): ValidationSection {
    const checks = (dimension.checks ?? []).map((check, i) => mapCheck(check, dimensionKey, i));

    // Sort: FAIL first, then WARNING, then PASS
    const rank: Record<ValidationStatus, number> = { FAIL: 0, WARNING: 1, PASS: 2 };
    checks.sort((a, b) => rank[a.status] - rank[b.status]);

    return {
        key: dimensionKey,
        label: dimensionLabel(dimensionKey),
        description: dimensionDescription(dimensionKey),
        checks,
    };
}


// -------------------------
// PUBLIC ENTRY POINT
// -------------------------

export function buildLayer1ValidationModel(
    data: Layer1FinalOutput,
    _facts: Layer1KeyFacts | null,
): ValidationModel {
    const dimensions = data.dimensions;

    // Build one section per dimension — order is whatever the engine sends
    const sections: ValidationSection[] = Object.entries(dimensions).map(
        ([key, dim]) => buildSection(key, dim),
    );

    const checks = sections.flatMap((s) => s.checks);
    const failures = checks.filter((c) => c.status === "FAIL");
    const warnings = checks.filter((c) => c.status === "WARNING");
    const blockerCount = failures.filter((c) => c.impact === "BLOCKER").length;
    const degradationCount = checks.filter(
        (c) => c.status === "WARNING" || (c.status === "FAIL" && c.impact === "DEGRADING"),
    ).length;

    let status: DecisionStatus = "ALLOWED";
    let tone: ValidationDecision["tone"] = "pass";
    if (failures.length > 0) {
        status = "BLOCKED";
        tone = "fail";
    } else if (warnings.length > 0) {
        status = "CONDITIONALLY ALLOWED";
        tone = "warning";
    }

    const message = status === "BLOCKED"
        ? `Dataset BLOCKED: ${blockerCount || failures.length} critical validation ${blockerCount === 1 ? "failure" : "failures"}`
        : status === "CONDITIONALLY ALLOWED"
            ? `Dataset CONDITIONALLY ALLOWED: ${warnings.length} validation ${warnings.length === 1 ? "warning" : "warnings"}`
            : "Dataset PASSED all structural checks";

    const decision: ValidationDecision = {
        status,
        tone,
        summary: `${failures.length}/${checks.length} validation checks failed`,
        message,
        confidence: checks.length >= 12 ? "High" : "Medium",
        checksRun: checks.length,
        failureCount: failures.length,
        blockerCount,
        warningCount: warnings.length,
        degradationCount,
    };

    return {
        sections,
        checks,
        failures,
        warnings,
        decision,
    };
}
