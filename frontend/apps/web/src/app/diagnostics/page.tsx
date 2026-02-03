"use client";

import { useState } from "react";
import { Activity, Play } from "lucide-react";
import { AnimatePresence } from "framer-motion";
import FileUpload from "@/components/file-upload";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/status-badge";
import { runAnalysis } from "@/lib/api";
import type { FileValidationResponse, Layer1OutputResponse } from "@/lib/api";

type DiagnosticState = "idle" | "file-uploaded" | "running" | "complete" | "error";

export default function DiagnosticsPage() {
    const [state, setState] = useState<DiagnosticState>("idle");
    const [uploadedFile, setUploadedFile] = useState<FileValidationResponse | null>(null);
    const [validationError, setValidationError] = useState<string | null>(null);
    const [analysisResult, setAnalysisResult] = useState<Layer1OutputResponse | null>(null);
    const [analysisError, setAnalysisError] = useState<string | null>(null);

    const handleFileValidated = (response: FileValidationResponse) => {
        if (response.is_valid) {
            setUploadedFile(response);
            setState("file-uploaded");
            setValidationError(null);
        } else {
            setValidationError(response.error || "File validation failed");
            setState("error");
        }
    };

    const handleRunAnalysis = async () => {
        setState("running");
        setAnalysisError(null);

        try {
            const result = await runAnalysis();
            setAnalysisResult(result);
            setState("complete");
        } catch (err) {
            setAnalysisError(err instanceof Error ? err.message : "Analysis failed");
            setState("error");
        }
    };

    return (
        <main className="flex-grow flex flex-col relative min-h-[calc(100vh-8rem)]">
            {/* Grid Pattern Background */}
            <div className="absolute inset-0 bg-grid-pattern pointer-events-none z-0" />

            <section className="relative z-10 flex flex-col items-center py-16 px-6">
                {/* Page Header */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center size-14 rounded-full bg-primary/10 text-primary mb-4">
                        <Activity className="size-7" />
                    </div>
                    <h1 className="text-3xl md:text-4xl font-bold tracking-tight mb-3 text-foreground">
                        Run Diagnostics
                    </h1>
                    <p className="text-muted-foreground font-mono max-w-lg mx-auto">
                        Upload your dataset to analyze data quality, detect anomalies,
                        and assess modeling readiness.
                    </p>
                </div>

                {/* Status Badge Section */}
                <div className="mb-6 min-h-[40px] flex items-center justify-center">
                    <AnimatePresence mode="wait">
                        {state === "idle" && (
                            <StatusBadge
                                key="idle"
                                status="info"
                                message="Awaiting File Upload"
                            />
                        )}
                        {state === "file-uploaded" && uploadedFile && (
                            <StatusBadge
                                key="success"
                                status="success"
                                message={`File Validated: ${uploadedFile.filename}`}
                            />
                        )}
                        {state === "running" && (
                            <StatusBadge
                                key="running"
                                status="loading"
                                message="Running Layer 1 Analysis..."
                            />
                        )}
                        {state === "complete" && (
                            <StatusBadge
                                key="complete"
                                status="success"
                                message="Analysis Complete"
                            />
                        )}
                        {state === "error" && (validationError || analysisError) && (
                            <StatusBadge
                                key="error"
                                status="error"
                                message={validationError || analysisError || "Error Occurred"}
                            />
                        )}
                    </AnimatePresence>
                </div>

                {/* File Upload Component */}
                <FileUpload onFileValidated={handleFileValidated} />

                {/* Run Analysis Button - Show when file is uploaded */}
                {(state === "file-uploaded" || state === "running") && (
                    <div className="mt-8 flex flex-col items-center gap-4">
                        <Button
                            size="lg"
                            onClick={handleRunAnalysis}
                            disabled={state === "running"}
                            className="gap-2 h-12 px-8"
                        >
                            {state === "running" ? (
                                <>
                                    <span className="animate-spin">⏳</span>
                                    Running Analysis...
                                </>
                            ) : (
                                <>
                                    <Play className="size-5" />
                                    Run Layer 1 Analysis
                                </>
                            )}
                        </Button>
                    </div>
                )}

                {/* Analysis Results */}
                {state === "complete" && analysisResult && (
                    <div className="mt-8 w-full max-w-4xl">
                        <div className="border border-border rounded-xl bg-card/80 backdrop-blur overflow-hidden">
                            {/* Results Header */}
                            <div className="px-6 py-4 border-b border-border bg-secondary/30">
                                <h2 className="text-xl font-semibold flex items-center gap-2">
                                    <Activity className="size-5 text-primary" />
                                    Layer 1 Analysis Results
                                </h2>
                                <p className="text-sm text-muted-foreground font-mono mt-1">
                                    Status: {analysisResult.status} • Shape: {analysisResult.shape.join(" × ")}
                                </p>
                            </div>

                            {/* Report */}
                            <div className="p-6">
                                <h3 className="font-semibold mb-3">Report</h3>
                                <pre className="bg-secondary/50 p-4 rounded-lg overflow-x-auto text-sm font-mono whitespace-pre-wrap text-muted-foreground">
                                    {analysisResult.report}
                                </pre>
                            </div>

                            {/* Signals Summary */}
                            <div className="px-6 pb-6">
                                <h3 className="font-semibold mb-3">Signals</h3>
                                <pre className="bg-secondary/50 p-4 rounded-lg overflow-x-auto text-sm font-mono text-muted-foreground max-h-64 overflow-y-auto">
                                    {JSON.stringify(analysisResult.signals, null, 2)}
                                </pre>
                            </div>
                        </div>
                    </div>
                )}

                {/* Bottom Status Info */}
                <div className="mt-8 flex flex-row gap-6 opacity-50">
                    <span className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">
                        Layer 1: Data Profiling
                    </span>
                    <span className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">
                        Pipeline: {state === "idle" ? "Ready" : state.replace("-", " ")}
                    </span>
                </div>
            </section>
        </main>
    );
}
