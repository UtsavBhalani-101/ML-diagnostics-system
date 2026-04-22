import type { DimensionResult, Layer1FinalOutput, Layer1KeyFacts } from "@/lib/api";

export type ValidationStatus = "PASS" | "FAIL" | "WARNING";
export type DecisionStatus = "ALLOWED" | "BLOCKED" | "CONDITIONALLY ALLOWED";
export type ImpactLevel = "BLOCKER" | "DEGRADING" | "INFORMATIONAL";

export interface ValidationCheck {
    id: string;
    dimensionKey: keyof Layer1FinalOutput["dimensions"];
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
    key: keyof Layer1FinalOutput["dimensions"];
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

type SignalMap = Record<string, unknown>;

const DIMENSION_LABELS: Record<keyof Layer1FinalOutput["dimensions"], string> = {
    data_integrity: "Data Integrity",
    target_viability: "Target Viability",
    sample_adequacy: "Sample Adequacy",
};

function isRecord(value: unknown): value is Record<string, unknown> {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function getNumber(signals: SignalMap, keys: string[], fallback = 0): number {
    for (const key of keys) {
        const value = signals[key];
        if (typeof value === "number" && Number.isFinite(value)) {
            return value;
        }
    }
    return fallback;
}

function getBoolean(signals: SignalMap, key: string): boolean {
    return signals[key] === true;
}

function getArray(signals: SignalMap, keys: string[]): string[] {
    for (const key of keys) {
        const value = signals[key];
        if (Array.isArray(value)) {
            return value.map(String);
        }
    }
    return [];
}

function getRatioObject(signals: SignalMap, key: string, ratioKey: string): Record<string, number> {
    const value = signals[key];
    if (!isRecord(value)) {
        return {};
    }

    const ratios = value[ratioKey];
    if (!isRecord(ratios)) {
        return {};
    }

    return Object.fromEntries(
        Object.entries(ratios).filter((entry): entry is [string, number] => typeof entry[1] === "number"),
    );
}

function getWorstRatio(signals: SignalMap, key: string, ratioKey: string, fallback = 0): number {
    const value = signals[key];
    if (isRecord(value) && typeof value.worst_ratio === "number") {
        return value.worst_ratio;
    }

    const ratios = getRatioObject(signals, key, ratioKey);
    const values = Object.values(ratios);
    return values.length > 0 ? Math.max(...values) : fallback;
}

function formatPercent(ratio: number): string {
    return `${(ratio * 100).toFixed(ratio > 0 && ratio < 0.01 ? 2 : 1)}%`;
}

function formatRatio(value: number): string {
    return value.toLocaleString(undefined, {
        maximumFractionDigits: value < 10 ? 2 : 1,
        minimumFractionDigits: value < 10 ? 2 : 0,
    });
}

function columnsWhere(ratios: Record<string, number>, predicate: (ratio: number) => boolean): string[] {
    return Object.entries(ratios)
        .filter(([, ratio]) => predicate(ratio))
        .sort((left, right) => right[1] - left[1])
        .map(([column, ratio]) => `${column} (${formatPercent(ratio)})`);
}

function statusByUpperBounds(value: number, warningAt: number, failAt: number): ValidationStatus {
    if (value >= failAt) {
        return "FAIL";
    }
    if (value >= warningAt) {
        return "WARNING";
    }
    return "PASS";
}

function statusByLowerBounds(value: number, failBelow: number, warningBelow: number): ValidationStatus {
    if (value < failBelow) {
        return "FAIL";
    }
    if (value < warningBelow) {
        return "WARNING";
    }
    return "PASS";
}

function makeCheck(input: Omit<ValidationCheck, "dimensionLabel">): ValidationCheck {
    return {
        ...input,
        dimensionLabel: DIMENSION_LABELS[input.dimensionKey],
    };
}

function dataIntegrityChecks(dimension: DimensionResult): ValidationCheck[] {
    const signals = dimension.signals;
    const totalColumns = Math.max(getNumber(signals, ["cols"], 0), 1);

    const mixedColumns = getArray(signals, ["mixed_type_columns"]);
    const mixedRatio = getNumber(signals, ["mixed_ratio"], mixedColumns.length / totalColumns);
    const mixedStatus: ValidationStatus = mixedColumns.length > 0 || mixedRatio > 0 ? "FAIL" : "PASS";

    const globalMissing = getNumber(signals, ["global_missing_ratio"], 0);
    const columnMissingRatios = getRatioObject(signals, "column_missing_ratio", "per_column");
    const worstColumnMissing = getWorstRatio(signals, "column_missing_ratio", "per_column");
    const hiddenRatios = getRatioObject(signals, "hidden_missing_ratio", "ratios");
    const hiddenWorst = getWorstRatio(signals, "hidden_missing_ratio", "ratios");
    const duplicateRatio = getNumber(signals, ["duplicate_ratio", "duplicated_ratio"], 0);
    const constantColumns = getArray(signals, ["constant_columns"]);
    const constantRatio = getNumber(signals, ["constant_ratio"], constantColumns.length / totalColumns);

    return [
        makeCheck({
            id: "data_integrity.mixed_types",
            dimensionKey: "data_integrity",
            testName: "Mixed Types",
            status: mixedStatus,
            observed: `${mixedColumns.length} columns (${formatPercent(mixedRatio)} affected)`,
            threshold: "0 columns",
            rule: "Must be 0 mixed-type columns",
            impact: "BLOCKER",
            reason: mixedStatus === "FAIL"
                ? "One or more columns contain values that cannot be represented by a single dtype."
                : "All inspected columns have a uniform dtype representation.",
            action: "Enforce a single dtype per offending column or split mixed semantic fields before modeling.",
            offendingColumns: mixedColumns,
        }),
        makeCheck({
            id: "data_integrity.global_missing",
            dimensionKey: "data_integrity",
            testName: "Global Missingness",
            status: statusByUpperBounds(globalMissing, 0.05, 0.2),
            observed: formatPercent(globalMissing),
            threshold: "PASS < 5%; WARNING < 20%; FAIL >= 20%",
            rule: "Dataset-wide missing cells must remain below 20%",
            impact: "DEGRADING",
            reason: "The total missing-cell ratio is checked against a deterministic upper bound.",
            action: "Impute missing values or remove fields/rows until dataset-wide missingness is below 20%.",
            optionalAction: "Document the missingness mechanism when the ratio is between 5% and 20%.",
            offendingColumns: [],
        }),
        makeCheck({
            id: "data_integrity.column_missing",
            dimensionKey: "data_integrity",
            testName: "Column Missingness",
            status: statusByUpperBounds(worstColumnMissing, 0.05, 0.2),
            observed: `${formatPercent(worstColumnMissing)} worst column`,
            threshold: "PASS < 5%; WARNING < 20%; FAIL >= 20%",
            rule: "No single column may have 20% or more missing values",
            impact: "DEGRADING",
            reason: "A high-missingness column can dominate preprocessing decisions and destabilize training data.",
            action: "Impute, remove, or recollect the offending columns until each column is below 20% missing.",
            optionalAction: "Review columns between 5% and 20% missing before training.",
            offendingColumns: columnsWhere(columnMissingRatios, (ratio) => ratio >= 0.2),
        }),
        makeCheck({
            id: "data_integrity.hidden_missing",
            dimensionKey: "data_integrity",
            testName: "Hidden Missing Tokens",
            status: statusByUpperBounds(hiddenWorst, 0.05, 0.15),
            observed: `${formatPercent(hiddenWorst)} worst text column`,
            threshold: "PASS < 5%; WARNING < 15%; FAIL >= 15%",
            rule: "Placeholder missing tokens must be standardized before validation",
            impact: "BLOCKER",
            reason: "String placeholders such as NA, unknown, ? or blank values are not normalized missing values.",
            action: "Convert placeholder tokens to nulls, then rerun validation and imputation.",
            optionalAction: "Standardize low-frequency placeholders even when below the warning threshold.",
            offendingColumns: columnsWhere(hiddenRatios, (ratio) => ratio >= 0.15),
        }),
        makeCheck({
            id: "data_integrity.duplicates",
            dimensionKey: "data_integrity",
            testName: "Duplicate Rows",
            status: statusByUpperBounds(duplicateRatio, 0.02, 0.15),
            observed: formatPercent(duplicateRatio),
            threshold: "PASS < 2%; WARNING < 15%; FAIL >= 15%",
            rule: "Duplicate row ratio must remain below 15%",
            impact: "DEGRADING",
            reason: "Duplicate rows reduce the effective sample count and can leak repeated observations into evaluation.",
            action: "Remove duplicated rows or justify repeated records as valid observations before modeling.",
            optionalAction: "Inspect duplicate provenance when the ratio is between 2% and 15%.",
            offendingColumns: [],
        }),
        makeCheck({
            id: "data_integrity.constant_columns",
            dimensionKey: "data_integrity",
            testName: "Constant Columns",
            status: statusByUpperBounds(constantRatio, Number.MIN_VALUE, 0.2),
            observed: `${constantColumns.length} columns (${formatPercent(constantRatio)} affected)`,
            threshold: "PASS = 0%; WARNING < 20%; FAIL >= 20%",
            rule: "Constant columns must not exceed 20% of the feature set",
            impact: "DEGRADING",
            reason: "Constant columns provide no learning signal and inflate the feature space.",
            action: "Drop constant columns before model training.",
            optionalAction: "Drop isolated constant columns even when the gate is only warning.",
            offendingColumns: constantColumns,
        }),
    ];
}

function targetViabilityChecks(dimension: DimensionResult): ValidationCheck[] {
    const signals = dimension.signals;
    const targetMissing = getNumber(signals, ["target_missing_ratio"], 0);
    const isDegenerate = getBoolean(signals, "target_degeneracy_flag");
    const dominantClassRatio = getNumber(signals, ["dominant_class_ratio"], 0);
    const contaminationRatio = getNumber(signals, ["type_contamination_ratio"], 0);
    const entropyRisk = getNumber(
        { ...dimension.breakdown.additive, ...dimension.breakdown.dominant },
        ["target_entropy_risk"],
        0,
    );
    const normalizedEntropy = Math.max(0, 1 - entropyRisk);

    return [
        makeCheck({
            id: "target_viability.target_missing",
            dimensionKey: "target_viability",
            testName: "Target Missingness",
            status: statusByUpperBounds(targetMissing, 0.1, 0.4),
            observed: formatPercent(targetMissing),
            threshold: "PASS <= 10%; WARNING <= 40%; FAIL > 40%",
            rule: "Target missing ratio must not exceed 40%",
            impact: "BLOCKER",
            reason: "Rows without target labels cannot be used for supervised validation.",
            action: "Remove unlabeled rows or recover target labels until target missingness is at or below 40%.",
            optionalAction: "Prefer resolving target missingness above 10% before training.",
            offendingColumns: [],
        }),
        makeCheck({
            id: "target_viability.degeneracy",
            dimensionKey: "target_viability",
            testName: "Target Degeneracy",
            status: isDegenerate ? "FAIL" : "PASS",
            observed: isDegenerate ? "Degenerate target" : "Target has multiple values",
            threshold: "At least 2 target values",
            rule: "Target must contain more than one non-null value",
            impact: "BLOCKER",
            reason: "A degenerate target has no learnable supervised distinction.",
            action: "Select a valid target column or recollect labels with more than one outcome.",
            offendingColumns: [],
        }),
        makeCheck({
            id: "target_viability.class_imbalance",
            dimensionKey: "target_viability",
            testName: "Class Imbalance",
            status: statusByUpperBounds(dominantClassRatio, 0.8, 0.95),
            observed: `${formatPercent(dominantClassRatio)} majority class`,
            threshold: "PASS <= 80%; WARNING <= 95%; FAIL > 95%",
            rule: "Dominant class must not exceed 95%",
            impact: "DEGRADING",
            reason: "A dominant class can make trivial predictions look valid while minority behavior is not learned.",
            action: "Rebalance labels, redefine the target, or collect minority-class examples before modeling.",
            optionalAction: "Use stratified validation and class-aware metrics when majority class exceeds 80%.",
            offendingColumns: [],
        }),
        makeCheck({
            id: "target_viability.entropy",
            dimensionKey: "target_viability",
            testName: "Target Entropy",
            status: statusByLowerBounds(normalizedEntropy, 0.5, 0.8),
            observed: `${formatPercent(normalizedEntropy)} normalized entropy`,
            threshold: "PASS >= 80%; WARNING >= 50%; FAIL < 50%",
            rule: "Target distribution must retain enough entropy to support learning",
            impact: "DEGRADING",
            reason: "Low target entropy indicates weak outcome diversity.",
            action: "Redefine the target or rebalance/recollect labels until normalized entropy is at least 50%.",
            optionalAction: "Review class distribution when normalized entropy is below 80%.",
            offendingColumns: [],
        }),
        makeCheck({
            id: "target_viability.type_contamination",
            dimensionKey: "target_viability",
            testName: "Target Type Contamination",
            status: statusByUpperBounds(contaminationRatio, 0.05, 0.1),
            observed: formatPercent(contaminationRatio),
            threshold: "PASS <= 5%; WARNING <= 10%; FAIL > 10%",
            rule: "Target values must use a consistent representation",
            impact: "BLOCKER",
            reason: "Mixed target representations can create false classes or invalid regression targets.",
            action: "Normalize target encoding to one dtype and one label vocabulary before modeling.",
            optionalAction: "Clean target representation drift above 5%.",
            offendingColumns: [],
        }),
    ];
}

function sampleAdequacyChecks(dimension: DimensionResult, facts: Layer1KeyFacts | null): ValidationCheck[] {
    const signals = dimension.signals;
    const rows = facts?.dimensions.rows ?? getNumber(signals, ["rows"], 0);
    const columns = facts?.dimensions.columns ?? getNumber(signals, ["cols"], 0);
    const samplesPerFeature = columns > 0 ? rows / columns : 0;
    const duplicateRatio = getNumber(signals, ["duplicated_ratio", "duplicate_ratio"], 0);
    const effectiveSampleScore = getNumber(signals, ["effective_sample_size", "effective_sample_score"], 0);
    const dependencyScore = getNumber(signals, ["sample_dependency_score"], 0);
    const featureVarianceRatio = getNumber(signals, ["feature_variance_score"], 0);
    const marginalCoverage = getNumber(signals, ["marginal_coverage"], 1);
    const jointCoverage = getNumber(signals, ["joint_coverage"], 1);

    return [
        makeCheck({
            id: "sample_adequacy.samples_per_feature",
            dimensionKey: "sample_adequacy",
            testName: "Samples per Feature",
            status: statusByLowerBounds(samplesPerFeature, 5, 10),
            observed: `${formatRatio(samplesPerFeature)} samples/feature`,
            threshold: "PASS >= 10; WARNING >= 5; FAIL < 5",
            rule: "Rows divided by columns must be at least 5",
            impact: "BLOCKER",
            reason: "The dataset has too few rows relative to the feature count.",
            action: "Collect more rows or reduce feature count until samples per feature is at least 5.",
            optionalAction: "Prefer at least 10 samples per feature for a clean pass.",
            offendingColumns: [],
        }),
        makeCheck({
            id: "sample_adequacy.duplicates",
            dimensionKey: "sample_adequacy",
            testName: "Effective Duplicate Load",
            status: statusByUpperBounds(duplicateRatio, 0.2, 0.5),
            observed: formatPercent(duplicateRatio),
            threshold: "PASS < 20%; WARNING < 50%; FAIL >= 50%",
            rule: "Duplicate rows must stay below 50% for effective sample support",
            impact: "BLOCKER",
            reason: "Excess duplication means nominal row count overstates independent evidence.",
            action: "Deduplicate or recollect independent observations before modeling.",
            optionalAction: "Inspect duplicate provenance when duplicate load exceeds 20%.",
            offendingColumns: [],
        }),
        makeCheck({
            id: "sample_adequacy.effective_sample",
            dimensionKey: "sample_adequacy",
            testName: "Effective Sample Separation",
            status: statusByLowerBounds(effectiveSampleScore, 0.23, 0.69),
            observed: formatRatio(effectiveSampleScore),
            threshold: "PASS >= 0.69; WARNING >= 0.23; FAIL < 0.23",
            rule: "Average nearest-neighbor distance must be at least 0.23",
            impact: "DEGRADING",
            reason: "Low nearest-neighbor separation means rows provide weak independent constraints.",
            action: "Collect more diverse samples or remove duplicated/near-duplicated observations.",
            optionalAction: "Review clustered samples when separation is below 0.69.",
            offendingColumns: [],
        }),
        makeCheck({
            id: "sample_adequacy.sample_dependency",
            dimensionKey: "sample_adequacy",
            testName: "Row Dependency",
            status: statusByLowerBounds(dependencyScore, 0.23, 0.69),
            observed: formatRatio(dependencyScore),
            threshold: "PASS >= 0.69; WARNING >= 0.23; FAIL < 0.23",
            rule: "Average adjacent-row distance must be at least 0.23",
            impact: "DEGRADING",
            reason: "Low adjacent-row distance suggests row order dependency or repeated observations.",
            action: "Remove dependent sequences or split the dataset by independent unit before modeling.",
            optionalAction: "Use group-aware validation when row dependency is suspected.",
            offendingColumns: [],
        }),
        makeCheck({
            id: "sample_adequacy.low_variance",
            dimensionKey: "sample_adequacy",
            testName: "Low-Variance Feature Ratio",
            status: statusByUpperBounds(featureVarianceRatio, 0.2, 0.5),
            observed: formatPercent(featureVarianceRatio),
            threshold: "PASS < 20%; WARNING < 50%; FAIL >= 50%",
            rule: "Low-variance features must stay below 50%",
            impact: "DEGRADING",
            reason: "Low-variance features inflate dimensionality without adding usable sample coverage.",
            action: "Drop or merge low-variance features until the low-variance ratio is below 50%.",
            optionalAction: "Review low-variance features once the ratio exceeds 20%.",
            offendingColumns: [],
        }),
        makeCheck({
            id: "sample_adequacy.marginal_coverage",
            dimensionKey: "sample_adequacy",
            testName: "Marginal Coverage",
            status: statusByLowerBounds(marginalCoverage, 0.4, 0.7),
            observed: formatPercent(marginalCoverage),
            threshold: "PASS >= 70%; WARNING >= 40%; FAIL < 40%",
            rule: "Average single-feature coverage must be at least 40%",
            impact: "BLOCKER",
            reason: "Feature distributions do not cover enough bins to support stable validation.",
            action: "Collect more representative data or reduce feature space until marginal coverage is at least 40%.",
            optionalAction: "Improve coverage toward 70% for a clean pass.",
            offendingColumns: [],
        }),
        makeCheck({
            id: "sample_adequacy.joint_coverage",
            dimensionKey: "sample_adequacy",
            testName: "Joint Coverage",
            status: statusByLowerBounds(jointCoverage, 0.3, 0.6),
            observed: formatPercent(jointCoverage),
            threshold: "PASS >= 60%; WARNING >= 30%; FAIL < 30%",
            rule: "Two-feature grid coverage must be at least 30%",
            impact: "BLOCKER",
            reason: "Sparse joint feature coverage leaves validation unsupported across feature combinations.",
            action: "Collect broader samples or reduce interacting features until joint coverage is at least 30%.",
            optionalAction: "Improve joint coverage toward 60% for a clean pass.",
            offendingColumns: [],
        }),
    ];
}

function sortChecks(checks: ValidationCheck[]): ValidationCheck[] {
    const rank: Record<ValidationStatus, number> = {
        FAIL: 0,
        WARNING: 1,
        PASS: 2,
    };
    return [...checks].sort((left, right) => rank[left.status] - rank[right.status]);
}

export function buildLayer1ValidationModel(
    data: Layer1FinalOutput,
    facts: Layer1KeyFacts | null,
): ValidationModel {
    const dimensions = data.dimensions;
    const sections: ValidationSection[] = [
        {
            key: "data_integrity",
            label: DIMENSION_LABELS.data_integrity,
            description: "Structural completeness, dtype consistency, and raw-table trust checks.",
            checks: sortChecks(dataIntegrityChecks(dimensions.data_integrity)),
        },
        {
            key: "target_viability",
            label: DIMENSION_LABELS.target_viability,
            description: "Target existence, consistency, and learnability checks.",
            checks: sortChecks(targetViabilityChecks(dimensions.target_viability)),
        },
        {
            key: "sample_adequacy",
            label: DIMENSION_LABELS.sample_adequacy,
            description: "Sample support, independence, and feature-space coverage checks.",
            checks: sortChecks(sampleAdequacyChecks(dimensions.sample_adequacy, facts)),
        },
    ];

    const checks = sections.flatMap((section) => section.checks);
    const failures = checks.filter((check) => check.status === "FAIL");
    const warnings = checks.filter((check) => check.status === "WARNING");
    const blockerCount = failures.filter((check) => check.impact === "BLOCKER").length;
    const degradationCount = checks.filter(
        (check) => check.status === "WARNING" || (check.status === "FAIL" && check.impact === "DEGRADING"),
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
