"use client";

import { Activity } from "lucide-react";
import FileUpload from "@/components/file-upload";

export default function DiagnosticsPage() {
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

                {/* File Upload Component */}
                <FileUpload />

                {/* Status Info */}
                <div className="mt-8 flex flex-row gap-6 opacity-50">
                    <span className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">
                        Layer 1: Data Profiling
                    </span>
                    <span className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">
                        Status: Awaiting Upload
                    </span>
                </div>
            </section>
        </main>
    );
}
