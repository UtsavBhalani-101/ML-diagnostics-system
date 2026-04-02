"use client";

import Link from "next/link";
import type { Route } from "next";
import { useRouter } from "next/navigation";
import { AnimatePresence } from "framer-motion";
import { Activity, ArrowRight, LoaderCircle, Play } from "lucide-react";
import FileUpload from "@/components/file-upload";
import TargetColumnSelector from "@/components/target-column-selector";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import type { FileValidationResponse } from "@/lib/api";
import { runAnalysis } from "@/lib/api";
import { useDiagnosticsStore } from "@/lib/diagnostics-store";

export default function DiagnosticsPage() {
    const router = useRouter();

    const state = useDiagnosticsStore((store) => store.state);
    const selectedFile = useDiagnosticsStore((store) => store.selectedFile);
    const uploadedFile = useDiagnosticsStore((store) => store.uploadedFile);
    const validationError = useDiagnosticsStore((store) => store.validationError);
    const analysisError = useDiagnosticsStore((store) => store.analysisError);
    const selectedTarget = useDiagnosticsStore((store) => store.selectedTarget);
    const targetConfirmed = useDiagnosticsStore((store) => store.targetConfirmed);

    const setState = useDiagnosticsStore((store) => store.setState);
    const setUploadedFile = useDiagnosticsStore((store) => store.setUploadedFile);
    const setValidationError = useDiagnosticsStore((store) => store.setValidationError);
    const setAnalysisResult = useDiagnosticsStore((store) => store.setAnalysisResult);
    const setAnalysisError = useDiagnosticsStore((store) => store.setAnalysisError);
    const resetAll = useDiagnosticsStore((store) => store.resetAll);

    const handleFileValidated = (response: FileValidationResponse) => {
        setUploadedFile(response);
        setState("file-uploaded");
        setValidationError(null);
        setAnalysisError(null);
    };

    const handleUploadReset = () => {
        resetAll();
    };

    const handleRunAnalysis = async () => {
        if (!selectedFile) {
            setAnalysisError("Please upload a valid dataset before running diagnostics.");
            setState("error");
            return;
        }

        setState("running");
        setAnalysisError(null);

        try {
            const result = await runAnalysis(selectedFile, selectedTarget);
            setAnalysisResult(result);
            setState("complete");
            router.push("/diagnostics/layer1-report");
        } catch (error) {
            setAnalysisError(error instanceof Error ? error.message : "Analysis failed");
            setState("error");
        }
    };

    const showTargetSelector =
        state === "file-uploaded" ||
        state === "target-selected" ||
        state === "running" ||
        state === "complete";

    const showRunButton =
        (state === "target-selected" || state === "running") && targetConfirmed;

    return (
        <main className="relative flex min-h-[calc(100vh-8rem)] flex-grow flex-col">
            <div className="pointer-events-none absolute inset-0 z-0 bg-grid-pattern" />

            <section className="relative z-10 flex flex-col items-center px-6 py-16">
                <div className="mb-8 text-center">
                    <div className="mb-4 inline-flex size-14 items-center justify-center rounded-full bg-primary/10 text-primary">
                        <Activity className="size-7" />
                    </div>
                    <h1 className="mb-3 text-3xl font-bold tracking-tight text-foreground md:text-4xl">
                        Run Diagnostics
                    </h1>
                    <p className="mx-auto max-w-lg font-mono text-muted-foreground">
                        Upload your dataset, confirm the target column, and run the live
                        Layer 1 pipeline against the backend.
                    </p>
                </div>

                <div className="mb-6 flex min-h-[40px] items-center justify-center">
                    <AnimatePresence mode="wait">
                        {state === "idle" && (
                            <StatusBadge key="idle" status="info" message="Awaiting File Upload" />
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
                                message={`Target: ${selectedTarget} - Ready to Analyze`}
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
                                message="Analysis Complete - Report Ready"
                            />
                        )}
                        {state === "error" && (validationError || analysisError) && (
                            <StatusBadge
                                key="error"
                                status="error"
                                message={validationError || analysisError || "Error occurred"}
                            />
                        )}
                    </AnimatePresence>
                </div>

                <FileUpload onFileValidated={handleFileValidated} onReset={handleUploadReset} />

                {showTargetSelector && <TargetColumnSelector />}

                {showRunButton && (
                    <div className="mt-8 flex flex-col items-center gap-4">
                        <Button
                            size="lg"
                            onClick={handleRunAnalysis}
                            disabled={state === "running"}
                            className="h-12 gap-2 px-8"
                        >
                            {state === "running" ? (
                                <>
                                    <LoaderCircle className="size-5 animate-spin" />
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

                {state === "complete" && (
                    <div className="mt-8 flex flex-col items-center gap-4">
                        <Link href={"/diagnostics/layer1-report" as Route}>
                            <Button size="lg" className="h-12 gap-2 px-8">
                                <ArrowRight className="size-5" />
                                View Layer 1 Report
                            </Button>
                        </Link>
                    </div>
                )}

                <div className="mt-8 flex flex-row gap-6 opacity-50">
                    <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                        Layer 1: Structural Risk
                    </span>
                    <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                        Pipeline: {state === "idle" ? "Ready" : state.replace("-", " ")}
                    </span>
                </div>
            </section>
        </main>
    );
}
