"use client";

import { motion } from "framer-motion";
import clsx from "clsx";

interface StatusBadgeProps {
    status: "success" | "error" | "warning" | "info" | "loading";
    message: string;
    className?: string;
}

const statusStyles = {
    success: {
        border: "border-emerald-500/30",
        bg: "bg-emerald-500/10",
        dot: "bg-emerald-500",
        text: "text-emerald-500",
    },
    error: {
        border: "border-red-500/30",
        bg: "bg-red-500/10",
        dot: "bg-red-500",
        text: "text-red-500",
    },
    warning: {
        border: "border-yellow-500/30",
        bg: "bg-yellow-500/10",
        dot: "bg-yellow-500",
        text: "text-yellow-500",
    },
    info: {
        border: "border-primary/30",
        bg: "bg-primary/10",
        dot: "bg-primary",
        text: "text-primary",
    },
    loading: {
        border: "border-primary/30",
        bg: "bg-primary/10",
        dot: "bg-primary",
        text: "text-primary",
    },
};

export function StatusBadge({ status, message, className }: StatusBadgeProps) {
    const styles = statusStyles[status];

    return (
        <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className={clsx("inline-block", className)}
        >
            <div
                className={clsx(
                    "inline-flex items-center gap-3 px-4 py-1.5 rounded-full border",
                    styles.border,
                    styles.bg
                )}
            >
                <span className="relative flex h-2 w-2">
                    {(status === "loading" || status === "info") && (
                        <span
                            className={clsx(
                                "animate-ping absolute inline-flex h-full w-full rounded-full opacity-75",
                                styles.dot
                            )}
                        />
                    )}
                    <span
                        className={clsx(
                            "relative inline-flex rounded-full h-2 w-2",
                            styles.dot
                        )}
                    />
                </span>
                <span
                    className={clsx(
                        "text-[10px] font-mono font-medium uppercase tracking-widest",
                        styles.text
                    )}
                >
                    {message}
                </span>
            </div>
        </motion.div>
    );
}
