"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle, ChevronDown, Loader, Search, Target, X } from "lucide-react";
import { getDatasetColumns, setTargetColumn } from "@/lib/api";
import { useDiagnosticsStore } from "@/lib/diagnostics-store";

export default function TargetColumnSelector() {
    const columns = useDiagnosticsStore((store) => store.columns);
    const suggestedTarget = useDiagnosticsStore((store) => store.suggestedTarget);
    const selectedTarget = useDiagnosticsStore((store) => store.selectedTarget);
    const targetConfirmed = useDiagnosticsStore((store) => store.targetConfirmed);
    const selectedFile = useDiagnosticsStore((store) => store.selectedFile);

    const setColumns = useDiagnosticsStore((store) => store.setColumns);
    const setSelectedTarget = useDiagnosticsStore((store) => store.setSelectedTarget);
    const setTargetConfirmed = useDiagnosticsStore((store) => store.setTargetConfirmed);
    const setState = useDiagnosticsStore((store) => store.setState);

    const [isOpen, setIsOpen] = useState(false);
    const [loading, setLoading] = useState(columns.length === 0);
    const [confirming, setConfirming] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState("");
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    useEffect(() => {
        if (isOpen) {
            document.documentElement.style.overflow = "hidden";
            document.body.style.overflow = "hidden";
        } else {
            document.documentElement.style.overflow = "";
            document.body.style.overflow = "";
        }

        return () => {
            document.documentElement.style.overflow = "";
            document.body.style.overflow = "";
        };
    }, [isOpen]);

    useEffect(() => {
        if (columns.length > 0) {
            setLoading(false);
            return;
        }

        async function fetchColumns() {
            if (!selectedFile) {
                setError("No file uploaded. Please upload a file first.");
                setLoading(false);
                return;
            }
            try {
                const response = await getDatasetColumns(selectedFile);
                setColumns(response.columns, response.suggested_target);
                if (response.suggested_target && !selectedTarget) {
                    setSelectedTarget(response.suggested_target);
                }
            } catch (fetchError) {
                setError(fetchError instanceof Error ? fetchError.message : "Failed to fetch columns");
            } finally {
                setLoading(false);
            }
        }

        fetchColumns();
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    const handleSelect = (column: string) => {
        setSelectedTarget(column);
        setTargetConfirmed(false);
        setIsOpen(false);
        setSearchQuery("");
    };

    const handleConfirm = async () => {
        if (!selectedTarget) return;

        setConfirming(true);
        setError(null);

        try {
            if (!selectedFile) {
                setError("No file uploaded. Please upload a file first.");
                return;
            }
            const response = await setTargetColumn(selectedFile, selectedTarget);
            if (response.valid) {
                setTargetConfirmed(true);
                setState("target-selected");
            } else {
                setError(response.message || "Invalid target column");
            }
        } catch (confirmError) {
            setError(confirmError instanceof Error ? confirmError.message : "Failed to set target column");
        } finally {
            setConfirming(false);
        }
    };

    const filteredColumns = columns.filter((column) =>
        column.toLowerCase().includes(searchQuery.toLowerCase())
    );

    if (loading) {
        return (
            <motion.div
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.35 }}
                className="mx-auto mt-6 w-full max-w-3xl"
            >
                <div className="flex items-center gap-4 rounded-xl border border-border bg-card/60 p-6 backdrop-blur">
                    <Loader className="size-5 animate-spin text-primary" />
                    <span className="font-mono text-sm text-muted-foreground">
                        Loading dataset columns...
                    </span>
                </div>
            </motion.div>
        );
    }

    return (
        <>
            <motion.div
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.35, delay: 0.1 }}
                className="mx-auto mt-6 w-full max-w-3xl"
            >
                <div className="rounded-xl border border-border bg-card/60 p-6 shadow-sm backdrop-blur">
                    <div className="mb-5 flex items-center gap-3">
                        <div className="flex size-10 shrink-0 items-center justify-center rounded-lg border border-primary/20 bg-primary/10">
                            <Target className="size-5 text-primary" />
                        </div>
                        <div>
                            <h3 className="text-base font-semibold text-foreground">
                                Select Target Column
                            </h3>
                            <p className="mt-0.5 font-mono text-sm text-muted-foreground">
                                Choose the column your model should predict.
                            </p>
                        </div>
                    </div>

                    <div className="mb-6">
                        <button
                            type="button"
                            onClick={() => setIsOpen(true)}
                            disabled={targetConfirmed}
                            className={`flex w-full items-center justify-between gap-3 rounded-lg border px-4 py-3 text-left transition-all duration-200 ${
                                targetConfirmed
                                    ? "border-emerald-500/30 bg-emerald-500/5"
                                    : "border-border bg-secondary/30 hover:border-primary/30 hover:bg-secondary/50"
                            }`}
                        >
                            <span
                                className={`truncate font-mono text-sm ${
                                    selectedTarget
                                        ? "font-medium text-foreground"
                                        : "text-muted-foreground"
                                }`}
                            >
                                {selectedTarget || "Select a column..."}
                            </span>
                            <div className="flex shrink-0 items-center gap-2">
                                {selectedTarget && suggestedTarget === selectedTarget && (
                                    <span className="rounded-full border border-primary/20 bg-primary/10 px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider text-primary">
                                        Suggested
                                    </span>
                                )}
                                {targetConfirmed ? (
                                    <CheckCircle className="size-4 text-emerald-500" />
                                ) : (
                                    <ChevronDown className="size-4 text-muted-foreground" />
                                )}
                            </div>
                        </button>
                    </div>

                    {error && (
                        <p className="mb-3 font-mono text-sm text-red-400">{error}</p>
                    )}

                    {targetConfirmed ? (
                        <div className="flex items-center gap-2 text-sm font-medium text-emerald-500">
                            <CheckCircle className="size-4" />
                            Target column set to <span className="font-mono font-bold">{selectedTarget}</span>
                        </div>
                    ) : (
                        <button
                            type="button"
                            onClick={handleConfirm}
                            disabled={!selectedTarget || confirming}
                            className={`inline-flex items-center gap-2 rounded-lg px-5 py-2.5 text-sm font-medium transition-all duration-200 ${
                                !selectedTarget || confirming
                                    ? "cursor-not-allowed bg-secondary/50 text-muted-foreground"
                                    : "bg-primary text-white shadow-sm hover:bg-primary/90"
                            }`}
                        >
                            {confirming ? (
                                <>
                                    <Loader className="size-4 animate-spin" />
                                    Setting target...
                                </>
                            ) : (
                                <>
                                    <Target className="size-4" />
                                    Confirm Target Column
                                </>
                            )}
                        </button>
                    )}
                </div>
            </motion.div>

            {mounted && createPortal(
                <AnimatePresence>
                    {isOpen && !targetConfirmed && (
                        <div
                            className="fixed inset-0 z-[150] flex items-center justify-center bg-background/80 p-4 backdrop-blur-sm"
                            data-lenis-prevent="true"
                        >
                            <motion.div
                                initial={{ opacity: 0, scale: 0.95, y: 10 }}
                                animate={{ opacity: 1, scale: 1, y: 0 }}
                                exit={{ opacity: 0, scale: 0.95, y: 10 }}
                                transition={{ duration: 0.2 }}
                                className="flex max-h-[85vh] w-full max-w-lg flex-col overflow-hidden rounded-xl border border-border bg-card shadow-2xl"
                            >
                                <div className="flex items-center justify-between border-b border-border bg-secondary/30 p-4">
                                    <h3 className="font-semibold text-foreground">Select Target Column</h3>
                                    <button
                                        onClick={() => setIsOpen(false)}
                                        className="rounded-md p-1 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
                                    >
                                        <X className="size-5" />
                                    </button>
                                </div>

                                {columns.length > 8 && (
                                    <div className="border-b border-border bg-card p-3">
                                        <div className="relative">
                                            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                                            <input
                                                type="text"
                                                placeholder="Search columns..."
                                                value={searchQuery}
                                                onChange={(event) => setSearchQuery(event.target.value)}
                                                className="w-full rounded-lg border border-border bg-secondary/30 py-2 pl-9 pr-4 font-mono text-sm text-foreground transition-colors placeholder:text-muted-foreground/50 focus:border-primary/40 focus:outline-none"
                                                autoFocus
                                            />
                                        </div>
                                    </div>
                                )}

                                <div className="min-h-[300px] flex-1 overflow-y-auto overscroll-contain p-2">
                                    {filteredColumns.length === 0 ? (
                                        <div className="p-4 text-center font-mono text-sm text-muted-foreground">
                                            No columns match "{searchQuery}"
                                        </div>
                                    ) : (
                                        <div className="space-y-1">
                                            {filteredColumns.map((column) => (
                                                <button
                                                    key={column}
                                                    type="button"
                                                    onClick={() => handleSelect(column)}
                                                    className={`flex w-full items-center justify-between rounded-lg border px-3 py-3 text-left font-mono text-sm transition-colors duration-150 ${
                                                        selectedTarget === column
                                                            ? "border-primary/20 bg-primary/10 font-medium text-primary"
                                                            : "border-transparent text-foreground hover:bg-secondary/80"
                                                    }`}
                                                >
                                                    <span className="truncate">{column}</span>
                                                    <div className="flex shrink-0 items-center gap-2">
                                                        {column === suggestedTarget && (
                                                            <span className="rounded-full border border-primary/10 bg-primary/10 px-2 py-0.5 font-mono text-[10px] uppercase text-primary/80">
                                                                suggested
                                                            </span>
                                                        )}
                                                        {selectedTarget === column && (
                                                            <CheckCircle className="size-4 text-primary" />
                                                        )}
                                                    </div>
                                                </button>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </motion.div>
                        </div>
                    )}
                </AnimatePresence>,
                document.body
            )}
        </>
    );
}
