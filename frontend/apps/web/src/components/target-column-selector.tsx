"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Target, ChevronDown, CheckCircle, Loader, Search, X } from "lucide-react";
import { getDatasetColumns, setTargetColumn } from "@/lib/api";
import { useDiagnosticsStore } from "@/lib/diagnostics-store";

export default function TargetColumnSelector() {
    const columns = useDiagnosticsStore((s) => s.columns);
    const suggestedTarget = useDiagnosticsStore((s) => s.suggestedTarget);
    const selectedTarget = useDiagnosticsStore((s) => s.selectedTarget);
    const targetConfirmed = useDiagnosticsStore((s) => s.targetConfirmed);

    const setColumns = useDiagnosticsStore((s) => s.setColumns);
    const setSelectedTarget = useDiagnosticsStore((s) => s.setSelectedTarget);
    const setTargetConfirmed = useDiagnosticsStore((s) => s.setTargetConfirmed);
    const setState = useDiagnosticsStore((s) => s.setState);

    const [isOpen, setIsOpen] = useState(false);
    const [loading, setLoading] = useState(columns.length === 0);
    const [confirming, setConfirming] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState("");

    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    // Lock body scroll when modal is open
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

    // Fetch columns on mount if not already loaded
    useEffect(() => {
        if (columns.length > 0) {
            setLoading(false);
            return;
        }

        async function fetchColumns() {
            try {
                const res = await getDatasetColumns();
                setColumns(res.columns, res.suggested_target);
                // Auto-select the suggested target
                if (res.suggested_target && !selectedTarget) {
                    setSelectedTarget(res.suggested_target);
                }
            } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to fetch columns");
            } finally {
                setLoading(false);
            }
        }
        fetchColumns();
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    const handleSelect = (col: string) => {
        setSelectedTarget(col);
        setTargetConfirmed(false);
        setIsOpen(false);
        setSearchQuery("");
    };

    const handleConfirm = async () => {
        if (!selectedTarget) return;
        setConfirming(true);
        setError(null);

        try {
            const res = await setTargetColumn(selectedTarget);
            if (res.valid) {
                setTargetConfirmed(true);
                setState("target-selected");
            } else {
                setError(res.message || "Invalid target column");
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to set target column");
        } finally {
            setConfirming(false);
        }
    };

    const filteredColumns = columns.filter((col) =>
        col.toLowerCase().includes(searchQuery.toLowerCase())
    );

    // ── Loading ──
    if (loading) {
        return (
            <motion.div
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.35 }}
                className="w-full max-w-3xl mx-auto mt-6"
            >
                <div className="rounded-xl border border-border bg-card/60 backdrop-blur p-6 flex items-center gap-4">
                    <Loader className="size-5 text-primary animate-spin" />
                    <span className="text-sm font-mono text-muted-foreground">
                        Loading dataset columns…
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
            className="w-full max-w-3xl mx-auto mt-6"
        >
            <div className="rounded-xl border border-border bg-card/60 backdrop-blur p-6 shadow-sm">
                {/* Header */}
                <div className="flex items-center gap-3 mb-5">
                    <div className="size-10 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center shrink-0">
                        <Target className="size-5 text-primary" />
                    </div>
                    <div>
                        <h3 className="text-base font-semibold text-foreground">
                            Select Target Column
                        </h3>
                        <p className="text-sm text-muted-foreground font-mono mt-0.5">
                            Choose the column your model should predict.
                        </p>
                    </div>
                </div>

                {/* Dropdown Trigger */}
                <div className="mb-6">
                    <button
                        type="button"
                        onClick={() => setIsOpen(true)}
                        disabled={targetConfirmed}
                        className={`w-full flex items-center justify-between gap-3 px-4 py-3 rounded-lg border text-left transition-all duration-200 cursor-pointer ${targetConfirmed
                            ? "border-emerald-500/30 bg-emerald-500/5"
                            : "border-border bg-secondary/30 hover:border-primary/30 hover:bg-secondary/50"
                            }`}
                    >
                        <span
                            className={`text-sm font-mono truncate ${selectedTarget
                                ? "text-foreground font-medium"
                                : "text-muted-foreground"
                                }`}
                        >
                            {selectedTarget || "Select a column…"}
                        </span>
                        <div className="flex items-center gap-2 shrink-0">
                            {selectedTarget && suggestedTarget === selectedTarget && (
                                <span className="text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20">
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

                {/* Error */}
                {error && (
                    <p className="text-sm text-red-400 font-mono mb-3">{error}</p>
                )}

                {/* Confirm / Status */}
                {targetConfirmed ? (
                    <div className="flex items-center gap-2 text-sm text-emerald-500 font-medium">
                        <CheckCircle className="size-4" />
                        Target column set to <span className="font-mono font-bold">{selectedTarget}</span>
                    </div>
                ) : (
                    <button
                        type="button"
                        onClick={handleConfirm}
                        disabled={!selectedTarget || confirming}
                        className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 cursor-pointer ${!selectedTarget || confirming
                            ? "bg-secondary/50 text-muted-foreground cursor-not-allowed"
                            : "bg-primary text-white hover:bg-primary/90 shadow-sm"
                            }`}
                    >
                        {confirming ? (
                            <>
                                <Loader className="size-4 animate-spin" />
                                Setting target…
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

        {/* Modal Overlay */}
        {/* Modal Overlay */}
        {mounted && createPortal(
            <AnimatePresence>
                {isOpen && !targetConfirmed && (
                    <div 
                        className="fixed inset-0 z-[150] flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm"
                        data-lenis-prevent="true"
                    >
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95, y: 10 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.95, y: 10 }}
                            transition={{ duration: 0.2 }}
                            className="w-full max-w-lg flex flex-col max-h-[85vh] rounded-xl border border-border bg-card shadow-2xl overflow-hidden"
                        >
                            {/* Modal Header */}
                            <div className="flex items-center justify-between p-4 border-b border-border bg-secondary/30">
                                <h3 className="font-semibold text-foreground">Select Target Column</h3>
                                <button
                                    onClick={() => setIsOpen(false)}
                                    className="p-1 rounded-md hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors"
                                >
                                    <X className="size-5" />
                                </button>
                            </div>

                            {/* Search */}
                            {columns.length > 8 && (
                                <div className="p-3 border-b border-border bg-card">
                                    <div className="relative">
                                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
                                        <input
                                            type="text"
                                            placeholder="Search columns…"
                                            value={searchQuery}
                                            onChange={(e) => setSearchQuery(e.target.value)}
                                            className="w-full pl-9 pr-4 py-2 text-sm font-mono bg-secondary/30 rounded-lg border border-border focus:outline-none focus:border-primary/40 text-foreground placeholder:text-muted-foreground/50 transition-colors"
                                            autoFocus
                                        />
                                    </div>
                                </div>
                            )}

                            {/* Columns List */}
                            <div className="flex-1 overflow-y-auto p-2 max-h-[60vh] min-h-[300px] overscroll-contain">
                                {filteredColumns.length === 0 ? (
                                    <div className="p-4 text-center text-sm text-muted-foreground font-mono">
                                        No columns match "{searchQuery}"
                                    </div>
                                ) : (
                                    <div className="space-y-1">
                                        {filteredColumns.map((col) => (
                                            <button
                                                key={col}
                                                type="button"
                                                onClick={() => handleSelect(col)}
                                                className={`w-full flex items-center justify-between px-3 py-3 rounded-lg text-left text-sm font-mono transition-colors duration-150 cursor-pointer ${selectedTarget === col
                                                    ? "bg-primary/10 text-primary font-medium border border-primary/20"
                                                    : "text-foreground hover:bg-secondary/80 border border-transparent"
                                                    }`}
                                            >
                                                <span className="truncate">{col}</span>
                                                <div className="flex items-center gap-2 shrink-0">
                                                    {col === suggestedTarget && (
                                                        <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-full bg-primary/10 text-primary/80 border border-primary/10">
                                                            suggested
                                                        </span>
                                                    )}
                                                    {selectedTarget === col && (
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
