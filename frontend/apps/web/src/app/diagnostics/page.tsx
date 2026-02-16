"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import type { Route } from "next";
import { Activity, Play, ArrowRight } from "lucide-react";
import { AnimatePresence } from "framer-motion";
import FileUpload from "@/components/file-upload";
import TargetColumnSelector from "@/components/target-column-selector";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/status-badge";
import { runAnalysis } from "@/lib/api";
import type { FileValidationResponse } from "@/lib/api";
import { useDiagnosticsStore } from "@/lib/diagnostics-store";

export default function DiagnosticsPage() {
    const router = useRouter();

    // ── Read all state from global store ──
    const state = useDiagnosticsStore((s) => s.state);
    const uploadedFile = useDiagnosticsStore((s) => s.uploadedFile);
    const validationError = useDiagnosticsStore((s) => s.validationError);
    const analysisError = useDiagnosticsStore((s) => s.analysisError);
    const selectedTarget = useDiagnosticsStore((s) => s.selectedTarget);
    const targetConfirmed = useDiagnosticsStore((s) => s.targetConfirmed);

    const setState = useDiagnosticsStore((s) => s.setState);
    const setUploadedFile = useDiagnosticsStore((s) => s.setUploadedFile);
    const setValidationError = useDiagnosticsStore((s) => s.setValidationError);
    const setAnalysisResult = useDiagnosticsStore((s) => s.setAnalysisResult);
    const setAnalysisError = useDiagnosticsStore((s) => s.setAnalysisError);
    const resetAll = useDiagnosticsStore((s) => s.resetAll);

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

    const handleUploadReset = () => {
        resetAll();
    };

    const handleRunAnalysis = async () => {
        setState("running");
        setAnalysisError(null);

        try {
            const result = await runAnalysis();
            setAnalysisResult(result);
            setState("complete");
            router.push("/diagnostics/layer1-report");
        } catch (err) {
            setAnalysisError(err instanceof Error ? err.message : "Analysis failed");
            setState("error");
        }
    };

    // Show the target column selector when file is uploaded (or beyond)
    const showTargetSelector =
        state === "file-uploaded" ||
        state === "target-selected" ||
        state === "running" ||
        state === "complete";

    // Show the Run Analysis button only when target is confirmed
    const showRunButton =
        (state === "target-selected" || state === "running") && targetConfirmed;

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
                                key="file-uploaded"
                                status="success"
                                message={`File Validated: ${uploadedFile.filename}`}
                            />
                        )}
                        {state === "target-selected" && selectedTarget && (
                            <StatusBadge
                                key="target-selected"
                                status="success"
                                message={`Target: ${selectedTarget} — Ready to Analyze`}
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
                                message="Analysis Complete — Report Ready"
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
                <FileUpload onFileValidated={handleFileValidated} onReset={handleUploadReset} />

                {/* Target Column Selector - Show after file is uploaded */}
                {showTargetSelector && <TargetColumnSelector />}

                {/* Run Analysis Button - Show when target is confirmed */}
                {showRunButton && (
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

                {/* View Report Button - Show when analysis is complete */}
                {state === "complete" && (
                    <div className="mt-8 flex flex-col items-center gap-4">
                        <Link href={"/diagnostics/layer1-report" as Route}>
                            <Button size="lg" className="gap-2 h-12 px-8">
                                <ArrowRight className="size-5" />
                                View Layer 1 Report
                            </Button>
                        </Link>
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
