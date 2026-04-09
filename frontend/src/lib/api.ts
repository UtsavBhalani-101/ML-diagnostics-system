/**
 * API Client for ML Diagnostics Backend
 * Base URL is read from NEXT_PUBLIC_API_URL env var.
 */

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/$/, "");

async function fetchAPI<T>(
    endpoint: string,
    options?: RequestInit,
): Promise<T> {
    const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

    const response = await fetch(url, {
        ...options,
        headers: {
            ...options?.headers,
        },
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Request failed" }));
        throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
}

export interface HomePageResponse {
    message: string;
    version: string;
    description: string;
    endpoints: Record<string, string>;
    workflow: string[];
}

export interface HealthResponse {
    status: string;
}

export interface SupportedExtensionsResponse {
    extensions: string[];
    count: number;
}

export interface FileValidationResponse {
    is_valid: boolean;
    filename: string;
    extension: string;
    error: string | null;
}

export interface DatasetColumnsResponse {
    filename: string;
    columns: string[];
    column_count: number;
    suggested_target: string;
}

export interface TargetColumnResponse {
    valid: boolean;
    target_column: string;
    message: string;
    available_columns: string[] | null;
}

export interface PrimaryIssue {
    name: string;
    risk: number;
    action: string;
}

export interface DimensionBreakdown {
    dominant: Record<string, number>;
    additive: Record<string, number>;
}

export interface DimensionResult {
    status: string;
    risk: number;
    breakdown: DimensionBreakdown;
    signals: Record<string, unknown>;
    primary_issues: PrimaryIssue[];
    interpretation: string;
}

export interface Layer1FinalOutput {
    overall: {
        status: string;
        risk: number;
        primary_failure_source: string | null;
        failing_dimensions: number;
        total_dimensions: number;
    };
    dimensions: {
        data_integrity: DimensionResult;
        target_viability: DimensionResult;
        sample_adequacy: DimensionResult;
    };
}

export interface Layer1KeyFacts {
    dimensions: {
        rows: number;
        columns: number;
        shape: string;
        scale_class: string;
    };
    memory: {
        memory_mb: number;
        memory_class: string;
    };
    feature_mix: {
        mix_type: string;
        num_ratio: number;
        cat_ratio: number;
    };
}

export interface Layer1OutputResponse {
    data_loaded: boolean;
    shape: number[];
    signals: Record<string, unknown>;
    logic: {
        facts: Layer1KeyFacts;
        dimensions: Record<string, unknown>;
    };
    final_output: Layer1FinalOutput;
    status: string;
}

export interface DocsResponse {
    overview: string;
    layers: {
        layer_1: {
            name: string;
            purpose: string;
            dimensions: {
                data_integrity: string;
                target_viability: string;
                sample_adequacy: string;
            };
            outputs: {
                risk_score: string;
                status: string;
                primary_causes: string;
                contributing_factors: string;
                quick_actions: string;
            };
        };
        layer_2: {
            status: string;
            message: string;
        };
    };
    interpretation: string;
    limitations: string;
}

export interface ModelsResponse {
    status: string;
    message: string;
    roadmap: string[];
}

export async function getHomePage(): Promise<HomePageResponse> {
    return fetchAPI<HomePageResponse>("/");
}

export async function getHealth(): Promise<HealthResponse> {
    return fetchAPI<HealthResponse>("/health");
}

export async function getSupportedExtensions(): Promise<SupportedExtensionsResponse> {
    return fetchAPI<SupportedExtensionsResponse>("/supported-extensions");
}

export async function validateFile(file: File): Promise<FileValidationResponse> {
    const formData = new FormData();
    formData.append("file", file);

    return fetchAPI<FileValidationResponse>("/validate-file", {
        method: "POST",
        body: formData,
    });
}

export async function getDatasetColumns(file: File): Promise<DatasetColumnsResponse> {
    const formData = new FormData();
    formData.append("file", file);

    return fetchAPI<DatasetColumnsResponse>("/dataset-columns", {
        method: "POST",
        body: formData,
    });
}

export async function setTargetColumn(file: File, targetColumn: string): Promise<TargetColumnResponse> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("target_column", targetColumn);

    return fetchAPI<TargetColumnResponse>("/set-target-column", {
        method: "POST",
        body: formData,
    });
}

export async function runAnalysis(file: File, targetColumn?: string | null): Promise<Layer1OutputResponse> {
    const formData = new FormData();
    formData.append("file", file);
    if (targetColumn) {
        formData.append("target_column", targetColumn);
    }

    return fetchAPI<Layer1OutputResponse>("/api/diagnostics/run", {
        method: "POST",
        body: formData,
    });
}

export async function getLayer1Output(): Promise<Layer1OutputResponse> {
    return fetchAPI<Layer1OutputResponse>("/layer-1-output");
}

export async function getDocsContent(): Promise<DocsResponse> {
    return fetchAPI<DocsResponse>("/api/docs");
}

export async function getModelsContent(): Promise<ModelsResponse> {
    return fetchAPI<ModelsResponse>("/api/models");
}

export { API_BASE_URL };
