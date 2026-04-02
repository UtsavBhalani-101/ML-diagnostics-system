"use client";

import { useRef, useState } from "react";
import type { ChangeEvent, DragEvent } from "react";
import { AnimatePresence, motion } from "framer-motion";
import clsx from "clsx";
import {
    AlertCircle,
    CheckCircle,
    File as FileIcon,
    Loader,
    RefreshCw,
    Trash2,
    UploadCloud,
} from "lucide-react";
import { validateFile } from "@/lib/api";
import type { FileValidationResponse } from "@/lib/api";
import { useDiagnosticsStore } from "@/lib/diagnostics-store";

type UploadStatus = "idle" | "uploading" | "success" | "error";

interface FileUploadProps {
    onFileValidated?: (response: FileValidationResponse) => void;
    onReset?: () => void;
}

export default function FileUpload({ onFileValidated, onReset }: FileUploadProps) {
    const storedStatus = useDiagnosticsStore((store) => store.fileUploadStatus);
    const storedFileName = useDiagnosticsStore((store) => store.fileName);
    const storedFileSize = useDiagnosticsStore((store) => store.fileSize);
    const storedExtension = useDiagnosticsStore((store) => store.fileExtension);
    const setFileUploadInfo = useDiagnosticsStore((store) => store.setFileUploadInfo);
    const setSelectedFile = useDiagnosticsStore((store) => store.setSelectedFile);

    const [status, setStatus] = useState<UploadStatus>(storedStatus);
    const [isDragging, setIsDragging] = useState(false);
    const [fileName, setFileName] = useState<string>(storedFileName);
    const [fileSize, setFileSize] = useState<number>(storedFileSize);
    const [progress, setProgress] = useState(storedStatus === "success" ? 100 : 0);
    const [errorMessage, setErrorMessage] = useState("");
    const [validationResponse, setValidationResponse] = useState<FileValidationResponse | null>(
        storedStatus === "success"
            ? { is_valid: true, filename: storedFileName, extension: storedExtension, saved: true, error: null }
            : null
    );
    const inputRef = useRef<HTMLInputElement>(null);

    const formatFileSize = (bytes: number): string => {
        if (!bytes) return "0 Bytes";
        const base = 1024;
        const units = ["Bytes", "KB", "MB", "GB"];
        const index = Math.floor(Math.log(bytes) / Math.log(base));
        return `${(bytes / Math.pow(base, index)).toFixed(2)} ${units[index]}`;
    };

    const handleFile = async (file: File) => {
        setStatus("uploading");
        setFileName(file.name);
        setFileSize(file.size);
        setProgress(0);
        setErrorMessage("");
        setValidationResponse(null);
        setSelectedFile(null);

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
            setStatus("success");
            setSelectedFile(file);
            setFileUploadInfo({
                status: "success",
                fileName: file.name,
                fileSize: file.size,
                fileExtension: response.extension,
            });

            if (onFileValidated) {
                onFileValidated(response);
            }

            if (navigator.vibrate) {
                navigator.vibrate(100);
            }
        } catch (error) {
            clearInterval(progressInterval);
            setProgress(100);
            setStatus("error");
            setSelectedFile(null);
            setErrorMessage(error instanceof Error ? error.message : "Upload failed. Please try again.");
            setFileUploadInfo({
                status: "error",
                fileName: file.name,
                fileSize: file.size,
                fileExtension: "",
            });
        }
    };

    const handleReset = () => {
        setStatus("idle");
        setFileName("");
        setFileSize(0);
        setProgress(0);
        setErrorMessage("");
        setValidationResponse(null);
        setSelectedFile(null);

        if (inputRef.current) {
            inputRef.current.value = "";
        }

        setFileUploadInfo({
            status: "idle",
            fileName: "",
            fileSize: 0,
            fileExtension: "",
        });

        if (onReset) {
            onReset();
        }
    };

    const onDrop = (event: DragEvent) => {
        event.preventDefault();
        setIsDragging(false);

        if (status === "uploading") return;

        const files = event.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]!);
        }
    };

    const onDragOver = (event: DragEvent) => {
        event.preventDefault();
        if (status !== "uploading") {
            setIsDragging(true);
        }
    };

    const onDragLeave = () => setIsDragging(false);

    const onSelect = (event: ChangeEvent<HTMLInputElement>) => {
        if (event.target.files && event.target.files.length > 0) {
            handleFile(event.target.files[0]!);
        }
    };

    return (
        <div className="mx-auto w-full max-w-3xl p-4 md:p-6">
            <AnimatePresence mode="wait">
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
                                "group relative cursor-pointer rounded-2xl border border-primary/10 bg-secondary/50 p-8 text-center shadow-sm backdrop-blur hover:shadow-md md:p-12",
                                isDragging && "border-primary ring-4 ring-primary/30"
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
                                        className="absolute -inset-4 rounded-full bg-primary/10 blur-md"
                                        style={{ display: isDragging ? "block" : "none" }}
                                    />
                                    <UploadCloud
                                        className={clsx(
                                            "h-16 w-16 drop-shadow-sm md:h-20 md:w-20",
                                            isDragging
                                                ? "text-primary"
                                                : "text-muted-foreground transition-colors duration-300 group-hover:text-primary"
                                        )}
                                    />
                                </motion.div>

                                <div className="space-y-2">
                                    <h3 className="text-xl font-semibold text-foreground md:text-2xl">
                                        {isDragging ? "Drop your file here" : "Upload your dataset"}
                                    </h3>
                                    <p className="mx-auto max-w-md text-muted-foreground md:text-lg">
                                        {isDragging ? (
                                            <span className="font-medium text-primary">Release to upload</span>
                                        ) : (
                                            <>
                                                Drag & drop a file here, or{" "}
                                                <span className="font-medium text-primary">browse</span>
                                            </>
                                        )}
                                    </p>
                                    <p className="font-mono text-sm text-muted-foreground/70">
                                        Supports CSV, Excel, Parquet, and JSON files - single file only
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

                {status === "uploading" && (
                    <motion.div
                        key="uploading"
                        initial={{ opacity: 0, y: 20, scale: 0.97 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: -10, scale: 0.95 }}
                        transition={{ type: "spring", stiffness: 300, damping: 24 }}
                        className="rounded-xl border border-primary/20 bg-card/80 px-5 py-5 shadow-md backdrop-blur"
                    >
                        <div className="flex items-start gap-4">
                            <div className="relative flex-shrink-0">
                                <div className="flex h-16 w-16 items-center justify-center rounded-lg border border-border bg-secondary/50 md:h-20 md:w-20">
                                    <FileIcon className="h-8 w-8 text-muted-foreground" />
                                </div>
                            </div>

                            <div className="min-w-0 flex-1">
                                <div className="mb-1 flex items-center gap-2">
                                    <FileIcon className="h-5 w-5 flex-shrink-0 text-primary" />
                                    <h4 className="truncate text-base font-medium text-foreground md:text-lg" title={fileName}>
                                        {fileName}
                                    </h4>
                                </div>
                                <div className="mb-3 flex items-center justify-between text-sm text-muted-foreground">
                                    <span className="font-mono text-xs md:text-sm">
                                        {formatFileSize(fileSize)}
                                    </span>
                                    <span className="flex items-center gap-1.5">
                                        <span className="font-medium">{Math.round(progress)}%</span>
                                        <Loader className="h-4 w-4 animate-spin text-primary" />
                                    </span>
                                </div>

                                <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
                                    <motion.div
                                        initial={{ width: 0 }}
                                        animate={{ width: `${progress}%` }}
                                        transition={{ duration: 0.4, type: "spring", stiffness: 100 }}
                                        className="h-full rounded-full bg-primary shadow-inner"
                                    />
                                </div>
                                <p className="mt-2 font-mono text-xs text-muted-foreground/70">
                                    Validating file...
                                </p>
                            </div>
                        </div>
                    </motion.div>
                )}

                {status === "success" && (
                    <motion.div
                        key="success"
                        initial={{ opacity: 0, y: 20, scale: 0.97 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: -10, scale: 0.95 }}
                        transition={{ type: "spring", stiffness: 300, damping: 24 }}
                        className="rounded-xl border border-emerald-500/30 bg-emerald-500/5 px-5 py-5 shadow-md backdrop-blur"
                    >
                        <div className="flex items-start gap-4">
                            <div className="relative flex-shrink-0">
                                <div className="flex h-16 w-16 items-center justify-center rounded-lg border border-emerald-500/20 bg-emerald-500/10 md:h-20 md:w-20">
                                    <FileIcon className="h-8 w-8 text-emerald-500" />
                                </div>
                                <motion.div
                                    initial={{ opacity: 0, scale: 0.5 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    transition={{ delay: 0.2, type: "spring", stiffness: 400, damping: 15 }}
                                    className="absolute -bottom-2 -right-2 rounded-full bg-background shadow-sm"
                                >
                                    <CheckCircle className="h-6 w-6 text-emerald-500" />
                                </motion.div>
                            </div>

                            <div className="min-w-0 flex-1">
                                <div className="mb-1 flex items-center gap-2">
                                    <h4 className="truncate text-base font-medium text-foreground md:text-lg" title={fileName}>
                                        {fileName}
                                    </h4>
                                </div>
                                <p className="mb-1 text-sm font-medium text-emerald-500">
                                    File validated and saved successfully
                                </p>
                                <div className="flex items-center gap-3 text-sm text-muted-foreground">
                                    <span className="font-mono text-xs md:text-sm">
                                        {formatFileSize(fileSize)}
                                        {validationResponse?.extension && ` - ${validationResponse.extension}`}
                                    </span>
                                </div>

                                <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-secondary">
                                    <motion.div
                                        initial={{ width: "90%" }}
                                        animate={{ width: "100%" }}
                                        transition={{ duration: 0.4 }}
                                        className="h-full rounded-full bg-emerald-500 shadow-inner"
                                    />
                                </div>

                                <button
                                    onClick={handleReset}
                                    className="mt-3 inline-flex items-center gap-1.5 rounded-md bg-secondary/80 px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors duration-200 hover:bg-secondary hover:text-destructive"
                                >
                                    <Trash2 className="h-3.5 w-3.5" />
                                    Remove and re-upload
                                </button>
                            </div>
                        </div>
                    </motion.div>
                )}

                {status === "error" && (
                    <motion.div
                        key="error"
                        initial={{ opacity: 0, y: 20, scale: 0.97 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: -10, scale: 0.95 }}
                        transition={{ type: "spring", stiffness: 300, damping: 24 }}
                        className="rounded-xl border border-red-500/30 bg-red-500/5 px-5 py-5 shadow-md backdrop-blur"
                    >
                        <div className="flex items-start gap-4">
                            <div className="relative flex-shrink-0">
                                <div className="flex h-16 w-16 items-center justify-center rounded-lg border border-red-500/20 bg-red-500/10 md:h-20 md:w-20">
                                    <FileIcon className="h-8 w-8 text-red-400" />
                                </div>
                                <motion.div
                                    initial={{ opacity: 0, scale: 0.5 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    transition={{ delay: 0.2, type: "spring", stiffness: 400, damping: 15 }}
                                    className="absolute -bottom-2 -right-2 rounded-full bg-background shadow-sm"
                                >
                                    <AlertCircle className="h-6 w-6 text-red-500" />
                                </motion.div>
                            </div>

                            <div className="min-w-0 flex-1">
                                <div className="mb-1 flex items-center gap-2">
                                    <h4 className="truncate text-base font-medium text-foreground md:text-lg" title={fileName}>
                                        {fileName}
                                    </h4>
                                </div>
                                <p className="mb-2 font-mono text-sm text-red-500">
                                    {errorMessage}
                                </p>
                                <div className="mb-3 flex items-center gap-3 text-sm text-muted-foreground">
                                    <span className="font-mono text-xs md:text-sm">
                                        {formatFileSize(fileSize)}
                                    </span>
                                </div>

                                <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
                                    <div className="h-full w-full rounded-full bg-red-500 shadow-inner" />
                                </div>

                                <button
                                    onClick={handleReset}
                                    className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-primary/10 px-4 py-2 text-sm font-medium text-primary transition-colors duration-200 hover:bg-primary/20"
                                >
                                    <RefreshCw className="h-4 w-4" />
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
