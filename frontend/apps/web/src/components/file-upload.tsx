"use client";

import { useState, useRef, DragEvent, ChangeEvent } from "react";
import { motion, AnimatePresence } from "framer-motion";
import clsx from "clsx";
import {
    UploadCloud,
    File as FileIcon,
    Loader,
    CheckCircle,
    AlertCircle,
    RefreshCw,
    Trash2,
} from "lucide-react";
import { validateFile, FileValidationResponse } from "@/lib/api";

type UploadStatus = "idle" | "uploading" | "success" | "error";

interface FileUploadProps {
    onFileValidated?: (response: FileValidationResponse) => void;
    onReset?: () => void;
}

export default function FileUpload({ onFileValidated, onReset }: FileUploadProps) {
    const [status, setStatus] = useState<UploadStatus>("idle");
    const [isDragging, setIsDragging] = useState(false);
    const [fileName, setFileName] = useState<string>("");
    const [fileSize, setFileSize] = useState<number>(0);
    const [progress, setProgress] = useState(0);
    const [errorMessage, setErrorMessage] = useState<string>("");
    const [validationResponse, setValidationResponse] = useState<FileValidationResponse | null>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    const formatFileSize = (bytes: number): string => {
        if (!bytes) return "0 Bytes";
        const k = 1024;
        const sizes = ["Bytes", "KB", "MB", "GB"];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
    };

    // Process the single file
    const handleFile = async (file: File) => {
        // Reset state
        setStatus("uploading");
        setFileName(file.name);
        setFileSize(file.size);
        setProgress(0);
        setErrorMessage("");
        setValidationResponse(null);

        // Simulate progress while uploading
        let currentProgress = 0;
        const progressInterval = setInterval(() => {
            currentProgress += Math.random() * 15;
            if (currentProgress > 90) currentProgress = 90;
            setProgress(Math.min(currentProgress, 90));
        }, 200);

        try {
            const response = await validateFile(file);
            clearInterval(progressInterval);
            setProgress(100);
            setValidationResponse(response);

            // Notify parent component for both valid and invalid results
            if (onFileValidated) {
                onFileValidated(response);
            }

            if (response.is_valid) {
                setStatus("success");
                // Haptic feedback on success
                if (navigator.vibrate) {
                    navigator.vibrate(100);
                }
            } else {
                setStatus("error");
                setErrorMessage(response.error || "File validation failed. Please upload a valid dataset file.");
            }
        } catch (error) {
            clearInterval(progressInterval);
            setProgress(100);
            setStatus("error");
            setErrorMessage(error instanceof Error ? error.message : "Upload failed. Please try again.");
        }
    };

    const handleReset = () => {
        setStatus("idle");
        setFileName("");
        setFileSize(0);
        setProgress(0);
        setErrorMessage("");
        setValidationResponse(null);
        if (inputRef.current) {
            inputRef.current.value = "";
        }
        if (onReset) {
            onReset();
        }
    };

    const onDrop = (e: DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        if (status === "uploading") return; // Prevent during upload

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]!); // Only take the first file
        }
    };

    const onDragOver = (e: DragEvent) => {
        e.preventDefault();
        if (status !== "uploading") {
            setIsDragging(true);
        }
    };

    const onDragLeave = () => setIsDragging(false);

    const onSelect = (e: ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            handleFile(e.target.files[0]!);
        }
    };

    return (
        <div className="w-full max-w-3xl mx-auto p-4 md:p-6">
            <AnimatePresence mode="wait">
                {/* ─── IDLE STATE: Show Drop Zone ─── */}
                {status === "idle" && (
                    <motion.div
                        key="dropzone"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        transition={{ duration: 0.3 }}
                    >
                        <motion.div
                            onDragOver={onDragOver}
                            onDragLeave={onDragLeave}
                            onDrop={onDrop}
                            onClick={() => inputRef.current?.click()}
                            initial={false}
                            animate={{
                                borderColor: isDragging ? "#135bec" : "#ffffff10",
                                scale: isDragging ? 1.02 : 1,
                            }}
                            whileHover={{ scale: 1.01 }}
                            transition={{ duration: 0.2 }}
                            className={clsx(
                                "relative rounded-2xl p-8 md:p-12 text-center cursor-pointer bg-secondary/50 border border-primary/10 shadow-sm hover:shadow-md backdrop-blur group",
                                isDragging && "ring-4 ring-primary/30 border-primary"
                            )}
                        >
                            <div className="flex flex-col items-center gap-5">
                                <motion.div
                                    animate={{ y: isDragging ? [-5, 0, -5] : 0 }}
                                    transition={{
                                        duration: 1.5,
                                        repeat: isDragging ? Infinity : 0,
                                        ease: "easeInOut",
                                    }}
                                    className="relative"
                                >
                                    <motion.div
                                        animate={{
                                            opacity: isDragging ? [0.5, 1, 0.5] : 1,
                                            scale: isDragging ? [0.95, 1.05, 0.95] : 1,
                                        }}
                                        transition={{
                                            duration: 2,
                                            repeat: isDragging ? Infinity : 0,
                                            ease: "easeInOut",
                                        }}
                                        className="absolute -inset-4 bg-primary/10 rounded-full blur-md"
                                        style={{ display: isDragging ? "block" : "none" }}
                                    />
                                    <UploadCloud
                                        className={clsx(
                                            "w-16 h-16 md:w-20 md:h-20 drop-shadow-sm",
                                            isDragging
                                                ? "text-primary"
                                                : "text-muted-foreground group-hover:text-primary transition-colors duration-300"
                                        )}
                                    />
                                </motion.div>

                                <div className="space-y-2">
                                    <h3 className="text-xl md:text-2xl font-semibold text-foreground">
                                        {isDragging ? "Drop your file here" : "Upload your dataset"}
                                    </h3>
                                    <p className="text-muted-foreground md:text-lg max-w-md mx-auto">
                                        {isDragging ? (
                                            <span className="font-medium text-primary">
                                                Release to upload
                                            </span>
                                        ) : (
                                            <>
                                                Drag & drop a file here, or{" "}
                                                <span className="text-primary font-medium">browse</span>
                                            </>
                                        )}
                                    </p>
                                    <p className="text-sm text-muted-foreground/70 font-mono">
                                        Supports CSV, Excel, Parquet, and JSON files • Single file only
                                    </p>
                                </div>

                                <input
                                    ref={inputRef}
                                    type="file"
                                    hidden
                                    onChange={onSelect}
                                    accept=".csv,.xlsx,.xls,.parquet,.json,.txt"
                                />
                            </div>
                        </motion.div>
                    </motion.div>
                )}

                {/* ─── UPLOADING STATE: Show Progress ─── */}
                {status === "uploading" && (
                    <motion.div
                        key="uploading"
                        initial={{ opacity: 0, y: 20, scale: 0.97 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: -10, scale: 0.95 }}
                        transition={{ type: "spring", stiffness: 300, damping: 24 }}
                        className="px-5 py-5 rounded-xl border border-primary/20 bg-card/80 backdrop-blur shadow-md"
                    >
                        <div className="flex items-start gap-4">
                            {/* File icon */}
                            <div className="relative flex-shrink-0">
                                <div className="w-16 h-16 md:w-20 md:h-20 rounded-lg bg-secondary/50 border border-border flex items-center justify-center">
                                    <FileIcon className="w-8 h-8 text-muted-foreground" />
                                </div>
                            </div>

                            {/* Info */}
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                    <FileIcon className="w-5 h-5 flex-shrink-0 text-primary" />
                                    <h4 className="font-medium text-base md:text-lg truncate text-foreground" title={fileName}>
                                        {fileName}
                                    </h4>
                                </div>
                                <div className="flex items-center justify-between text-sm text-muted-foreground mb-3">
                                    <span className="text-xs md:text-sm font-mono">
                                        {formatFileSize(fileSize)}
                                    </span>
                                    <span className="flex items-center gap-1.5">
                                        <span className="font-medium">{Math.round(progress)}%</span>
                                        <Loader className="w-4 h-4 animate-spin text-primary" />
                                    </span>
                                </div>

                                {/* Progress bar */}
                                <div className="w-full h-2 bg-secondary rounded-full overflow-hidden">
                                    <motion.div
                                        initial={{ width: 0 }}
                                        animate={{ width: `${progress}%` }}
                                        transition={{ duration: 0.4, type: "spring", stiffness: 100 }}
                                        className="h-full rounded-full bg-primary shadow-inner"
                                    />
                                </div>
                                <p className="text-xs text-muted-foreground/70 mt-2 font-mono">
                                    Validating file...
                                </p>
                            </div>
                        </div>
                    </motion.div>
                )}

                {/* ─── SUCCESS STATE ─── */}
                {status === "success" && (
                    <motion.div
                        key="success"
                        initial={{ opacity: 0, y: 20, scale: 0.97 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: -10, scale: 0.95 }}
                        transition={{ type: "spring", stiffness: 300, damping: 24 }}
                        className="px-5 py-5 rounded-xl border border-emerald-500/30 bg-emerald-500/5 backdrop-blur shadow-md"
                    >
                        <div className="flex items-start gap-4">
                            {/* File icon with success badge */}
                            <div className="relative flex-shrink-0">
                                <div className="w-16 h-16 md:w-20 md:h-20 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                                    <FileIcon className="w-8 h-8 text-emerald-500" />
                                </div>
                                <motion.div
                                    initial={{ opacity: 0, scale: 0.5 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    transition={{ delay: 0.2, type: "spring", stiffness: 400, damping: 15 }}
                                    className="absolute -right-2 -bottom-2 bg-background rounded-full shadow-sm"
                                >
                                    <CheckCircle className="w-6 h-6 text-emerald-500" />
                                </motion.div>
                            </div>

                            {/* Info */}
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                    <h4 className="font-medium text-base md:text-lg truncate text-foreground" title={fileName}>
                                        {fileName}
                                    </h4>
                                </div>
                                <p className="text-sm text-emerald-500 font-medium mb-1">
                                    ✓ File validated and saved successfully
                                </p>
                                <div className="flex items-center gap-3 text-sm text-muted-foreground">
                                    <span className="text-xs md:text-sm font-mono">
                                        {formatFileSize(fileSize)}
                                        {validationResponse?.extension && ` • ${validationResponse.extension}`}
                                    </span>
                                </div>

                                {/* Completed progress bar */}
                                <div className="w-full h-2 bg-secondary rounded-full overflow-hidden mt-3">
                                    <motion.div
                                        initial={{ width: "90%" }}
                                        animate={{ width: "100%" }}
                                        transition={{ duration: 0.4 }}
                                        className="h-full rounded-full bg-emerald-500 shadow-inner"
                                    />
                                </div>

                                {/* Remove button */}
                                <button
                                    onClick={handleReset}
                                    className="mt-3 inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-md bg-secondary/80 hover:bg-secondary text-muted-foreground hover:text-destructive transition-colors duration-200"
                                >
                                    <Trash2 className="w-3.5 h-3.5" />
                                    Remove & Re-upload
                                </button>
                            </div>
                        </div>
                    </motion.div>
                )}

                {/* ─── ERROR STATE ─── */}
                {status === "error" && (
                    <motion.div
                        key="error"
                        initial={{ opacity: 0, y: 20, scale: 0.97 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: -10, scale: 0.95 }}
                        transition={{ type: "spring", stiffness: 300, damping: 24 }}
                        className="px-5 py-5 rounded-xl border border-red-500/30 bg-red-500/5 backdrop-blur shadow-md"
                    >
                        <div className="flex items-start gap-4">
                            {/* File icon with error badge */}
                            <div className="relative flex-shrink-0">
                                <div className="w-16 h-16 md:w-20 md:h-20 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center justify-center">
                                    <FileIcon className="w-8 h-8 text-red-400" />
                                </div>
                                <motion.div
                                    initial={{ opacity: 0, scale: 0.5 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    transition={{ delay: 0.2, type: "spring", stiffness: 400, damping: 15 }}
                                    className="absolute -right-2 -bottom-2 bg-background rounded-full shadow-sm"
                                >
                                    <AlertCircle className="w-6 h-6 text-red-500" />
                                </motion.div>
                            </div>

                            {/* Info */}
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                    <h4 className="font-medium text-base md:text-lg truncate text-foreground" title={fileName}>
                                        {fileName}
                                    </h4>
                                </div>
                                <p className="text-sm text-red-500 font-mono mb-2">
                                    {errorMessage}
                                </p>
                                <div className="flex items-center gap-3 text-sm text-muted-foreground mb-3">
                                    <span className="text-xs md:text-sm font-mono">
                                        {formatFileSize(fileSize)}
                                    </span>
                                </div>

                                {/* Failed progress bar */}
                                <div className="w-full h-2 bg-secondary rounded-full overflow-hidden">
                                    <div className="h-full rounded-full bg-red-500 shadow-inner w-full" />
                                </div>

                                {/* Try Again button */}
                                <button
                                    onClick={handleReset}
                                    className="mt-3 inline-flex items-center gap-1.5 text-sm font-medium px-4 py-2 rounded-lg bg-primary/10 hover:bg-primary/20 text-primary transition-colors duration-200"
                                >
                                    <RefreshCw className="w-4 h-4" />
                                    Try Again
                                </button>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
