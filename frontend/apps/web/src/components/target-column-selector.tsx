"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Target, ChevronDown, CheckCircle, Loader, Search } from "lucide-react";
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

                {/* Dropdown */}
                <div className="relative mb-4">
                    <button
                        type="button"
                        onClick={() => setIsOpen(!isOpen)}
                        disabled={targetConfirmed}
                        className={`w-full flex items-center justify-between gap-3 px-4 py-3 rounded-lg border text-left transition-all duration-200 cursor-pointer ${targetConfirmed
                                ? "border-emerald-500/30 bg-emerald-500/5"
                                : isOpen
                                    ? "border-primary/50 bg-primary/5 ring-2 ring-primary/20"
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
                                <ChevronDown
                                    className={`size-4 text-muted-foreground transition-transform duration-200 ${isOpen ? "rotate-180" : ""
                                        }`}
                                />
                            )}
                        </div>
                    </button>

                    {/* Dropdown List */}
                    {isOpen && !targetConfirmed && (
                        <motion.div
                            initial={{ opacity: 0, y: -4, scale: 0.98 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: -4, scale: 0.98 }}
                            transition={{ duration: 0.15 }}
                            className="absolute z-20 mt-2 w-full rounded-lg border border-border bg-card shadow-xl backdrop-blur-lg overflow-hidden"
                        >
                            {/* Search */}
                            {columns.length > 8 && (
                                <div className="p-2 border-b border-border">
                                    <div className="relative">
                                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-3.5 text-muted-foreground" />
                                        <input
                                            type="text"
                                            placeholder="Search columns…"
                                            value={searchQuery}
                                            onChange={(e) => setSearchQuery(e.target.value)}
                                            className="w-full pl-8 pr-3 py-2 text-sm font-mono bg-secondary/30 rounded-md border border-border focus:outline-none focus:border-primary/40 text-foreground placeholder:text-muted-foreground/50"
                                            autoFocus
                                        />
                                    </div>
                                </div>
                            )}

                            <div className="max-h-52 overflow-y-auto">
                                {filteredColumns.length === 0 ? (
                                    <div className="px-4 py-3 text-sm text-muted-foreground font-mono">
                                        No columns match "{searchQuery}"
                                    </div>
                                ) : (
                                    filteredColumns.map((col) => (
                                        <button
                                            key={col}
                                            type="button"
                                            onClick={() => handleSelect(col)}
                                            className={`w-full flex items-center justify-between px-4 py-2.5 text-left text-sm font-mono transition-colors duration-100 cursor-pointer ${selectedTarget === col
                                                    ? "bg-primary/10 text-primary"
                                                    : "text-foreground hover:bg-secondary/60"
                                                }`}
                                        >
                                            <span className="truncate">{col}</span>
                                            <div className="flex items-center gap-2 shrink-0">
                                                {col === suggestedTarget && (
                                                    <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-primary/10 text-primary/70">
                                                        suggested
                                                    </span>
                                                )}
                                                {selectedTarget === col && (
                                                    <CheckCircle className="size-3.5 text-primary" />
                                                )}
                                            </div>
                                        </button>
                                    ))
                                )}
                            </div>
                        </motion.div>
                    )}
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
    );
}
