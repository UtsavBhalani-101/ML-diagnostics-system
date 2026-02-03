"use client";

import { useState, useRef, DragEvent, ChangeEvent } from "react";
import { motion, AnimatePresence } from "framer-motion";
import clsx from "clsx";
import {
    UploadCloud,
    File as FileIcon,
    Trash2,
    Loader,
    CheckCircle,
    AlertCircle,
} from "lucide-react";
import { validateFile, FileValidationResponse } from "@/lib/api";

interface FileWithPreview {
    id: string;
    preview: string;
    progress: number;
    name: string;
    size: number;
    type: string;
    lastModified?: number;
    file?: File;
    status: "uploading" | "success" | "error";
    error?: string;
    response?: FileValidationResponse;
}

interface FileUploadProps {
    onFileValidated?: (response: FileValidationResponse) => void;
}

export default function FileUpload({ onFileValidated }: FileUploadProps) {
    const [files, setFiles] = useState<FileWithPreview[]>([]);
    const [isDragging, setIsDragging] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);

    // Process dropped or selected files
    const handleFiles = async (fileList: FileList) => {
        const newFiles = Array.from(fileList).map((file) => ({
            id: `${URL.createObjectURL(file)}-${Date.now()}`,
            preview: URL.createObjectURL(file),
            progress: 0,
            name: file.name,
            size: file.size,
            type: file.type,
            lastModified: file.lastModified,
            file,
            status: "uploading" as const,
        }));

        setFiles((prev) => [...prev, ...newFiles]);

        // Upload each file to the backend
        for (const fileItem of newFiles) {
            await uploadFile(fileItem);
        }
    };

    // Upload file to backend
    const uploadFile = async (fileItem: FileWithPreview) => {
        if (!fileItem.file) return;

        // Simulate progress while uploading
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += Math.random() * 20;
            if (progress > 90) progress = 90; // Cap at 90% until actual completion
            setFiles((prev) =>
                prev.map((f) =>
                    f.id === fileItem.id ? { ...f, progress: Math.min(progress, 90) } : f
                )
            );
        }, 200);

        try {
            // Call the backend API
            const response = await validateFile(fileItem.file);

            clearInterval(progressInterval);

            // Update file status based on response
            setFiles((prev) =>
                prev.map((f) =>
                    f.id === fileItem.id
                        ? {
                            ...f,
                            progress: 100,
                            status: response.is_valid ? "success" : "error",
                            error: response.error || undefined,
                            response,
                        }
                        : f
                )
            );

            // Notify parent component
            if (response.is_valid && onFileValidated) {
                onFileValidated(response);
            }

            // Haptic feedback on success
            if (response.is_valid && navigator.vibrate) {
                navigator.vibrate(100);
            }
        } catch (error) {
            clearInterval(progressInterval);

            setFiles((prev) =>
                prev.map((f) =>
                    f.id === fileItem.id
                        ? {
                            ...f,
                            progress: 100,
                            status: "error",
                            error: error instanceof Error ? error.message : "Upload failed",
                        }
                        : f
                )
            );
        }
    };

    const onDrop = (e: DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        handleFiles(e.dataTransfer.files);
    };

    const onDragOver = (e: DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const onDragLeave = () => setIsDragging(false);

    const onSelect = (e: ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) handleFiles(e.target.files);
    };

    const formatFileSize = (bytes: number): string => {
        if (!bytes) return "0 Bytes";
        const k = 1024;
        const sizes = ["Bytes", "KB", "MB", "GB"];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
    };

    const removeFile = (id: string) => {
        setFiles((prev) => prev.filter((f) => f.id !== id));
    };

    return (
        <div className="w-full max-w-3xl mx-auto p-4 md:p-6">
            {/* Drop zone */}
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
                            {isDragging
                                ? "Drop files here"
                                : files.length
                                    ? "Add more files"
                                    : "Upload your dataset"}
                        </h3>
                        <p className="text-muted-foreground md:text-lg max-w-md mx-auto">
                            {isDragging ? (
                                <span className="font-medium text-primary">
                                    Release to upload
                                </span>
                            ) : (
                                <>
                                    Drag & drop files here, or{" "}
                                    <span className="text-primary font-medium">browse</span>
                                </>
                            )}
                        </p>
                        <p className="text-sm text-muted-foreground/70 font-mono">
                            Supports CSV, Excel, Parquet, and JSON files
                        </p>
                    </div>

                    <input
                        ref={inputRef}
                        type="file"
                        multiple
                        hidden
                        onChange={onSelect}
                        accept=".csv,.xlsx,.xls,.parquet,.json,.txt"
                    />
                </div>
            </motion.div>

            {/* Uploaded files list */}
            <div className="mt-8">
                <AnimatePresence>
                    {files.length > 0 && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="flex justify-between items-center mb-3 px-2"
                        >
                            <h3 className="font-semibold text-lg md:text-xl text-foreground">
                                Uploaded files ({files.length})
                            </h3>
                            {files.length > 1 && (
                                <button
                                    onClick={() => setFiles([])}
                                    className="text-sm font-medium px-3 py-1 bg-secondary hover:bg-secondary/80 rounded-md text-muted-foreground hover:text-destructive transition-colors duration-200"
                                >
                                    Clear all
                                </button>
                            )}
                        </motion.div>
                    )}
                </AnimatePresence>

                <div
                    className={clsx(
                        "flex flex-col gap-3 overflow-y-auto pr-2",
                        files.length > 3 && "max-h-96"
                    )}
                >
                    <AnimatePresence>
                        {files.map((file) => (
                            <motion.div
                                key={file.id}
                                initial={{ opacity: 0, y: 20, scale: 0.97 }}
                                animate={{ opacity: 1, y: 0, scale: 1 }}
                                exit={{ opacity: 0, y: -20, scale: 0.95 }}
                                transition={{ type: "spring", stiffness: 300, damping: 24 }}
                                className={clsx(
                                    "px-4 py-4 flex items-start gap-4 rounded-xl border shadow hover:shadow-md transition-all duration-200",
                                    file.status === "error"
                                        ? "bg-red-500/10 border-red-500/30"
                                        : "bg-card/80 border-border"
                                )}
                            >
                                {/* Thumbnail */}
                                <div className="relative flex-shrink-0">
                                    <div className="w-16 h-16 md:w-20 md:h-20 rounded-lg bg-secondary/50 border border-border flex items-center justify-center">
                                        <FileIcon className="w-8 h-8 text-muted-foreground" />
                                    </div>
                                    {file.status === "success" && (
                                        <motion.div
                                            initial={{ opacity: 0, scale: 0.5 }}
                                            animate={{ opacity: 1, scale: 1 }}
                                            className="absolute -right-2 -bottom-2 bg-background rounded-full shadow-sm"
                                        >
                                            <CheckCircle className="w-5 h-5 text-emerald-500" />
                                        </motion.div>
                                    )}
                                    {file.status === "error" && (
                                        <motion.div
                                            initial={{ opacity: 0, scale: 0.5 }}
                                            animate={{ opacity: 1, scale: 1 }}
                                            className="absolute -right-2 -bottom-2 bg-background rounded-full shadow-sm"
                                        >
                                            <AlertCircle className="w-5 h-5 text-red-500" />
                                        </motion.div>
                                    )}
                                </div>

                                {/* File info & progress */}
                                <div className="flex-1 min-w-0">
                                    <div className="flex flex-col gap-1 w-full">
                                        {/* Filename */}
                                        <div className="flex items-center gap-2 min-w-0">
                                            <FileIcon className="w-5 h-5 flex-shrink-0 text-primary" />
                                            <h4
                                                className="font-medium text-base md:text-lg truncate text-foreground"
                                                title={file.name}
                                            >
                                                {file.name}
                                            </h4>
                                        </div>

                                        {/* Error message */}
                                        {file.error && (
                                            <p className="text-sm text-red-500 font-mono">
                                                {file.error}
                                            </p>
                                        )}

                                        {/* Details & remove/loading */}
                                        <div className="flex items-center justify-between gap-3 text-sm text-muted-foreground">
                                            <span className="text-xs md:text-sm font-mono">
                                                {formatFileSize(file.size)}
                                                {file.response?.extension && ` • ${file.response.extension}`}
                                            </span>
                                            <span className="flex items-center gap-1.5">
                                                <span className="font-medium">
                                                    {Math.round(file.progress)}%
                                                </span>
                                                {file.status === "uploading" ? (
                                                    <Loader className="w-4 h-4 animate-spin text-primary" />
                                                ) : (
                                                    <Trash2
                                                        className="w-4 h-4 cursor-pointer text-muted-foreground hover:text-destructive transition-colors duration-200"
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            removeFile(file.id);
                                                        }}
                                                        aria-label="Remove file"
                                                    />
                                                )}
                                            </span>
                                        </div>
                                    </div>

                                    {/* Progress bar */}
                                    <div className="w-full h-2 bg-secondary rounded-full overflow-hidden mt-3">
                                        <motion.div
                                            initial={{ width: 0 }}
                                            animate={{ width: `${file.progress}%` }}
                                            transition={{
                                                duration: 0.4,
                                                type: "spring",
                                                stiffness: 100,
                                                ease: "easeOut",
                                            }}
                                            className={clsx(
                                                "h-full rounded-full shadow-inner",
                                                file.status === "error"
                                                    ? "bg-red-500"
                                                    : file.status === "success"
                                                        ? "bg-emerald-500"
                                                        : "bg-primary"
                                            )}
                                        />
                                    </div>
                                </div>
                            </motion.div>
                        ))}
                    </AnimatePresence>
                </div>
            </div>
        </div>
    );
}
