import { create } from "zustand";
import type { FileValidationResponse, Layer1OutputResponse } from "@/lib/api";

export type DiagnosticState =
    | "idle"
    | "file-uploaded"
    | "target-selected"
    | "running"
    | "complete"
    | "error";

interface DiagnosticsStore {
    // Page-level state
    state: DiagnosticState;
    selectedFile: File | null;
    uploadedFile: FileValidationResponse | null;
    validationError: string | null;
    analysisResult: Layer1OutputResponse | null;
    analysisError: string | null;

    // FileUpload component persisted state
    fileUploadStatus: "idle" | "uploading" | "success" | "error";
    fileName: string;
    fileSize: number;
    fileExtension: string;

    // Target column state
    columns: string[];
    suggestedTarget: string;
    selectedTarget: string | null;
    targetConfirmed: boolean;

    // Actions
    setState: (state: DiagnosticState) => void;
    setSelectedFile: (file: File | null) => void;
    setUploadedFile: (file: FileValidationResponse | null) => void;
    setValidationError: (error: string | null) => void;
    setAnalysisResult: (result: Layer1OutputResponse | null) => void;
    setAnalysisError: (error: string | null) => void;

    setFileUploadInfo: (info: {
        status: "idle" | "uploading" | "success" | "error";
        fileName: string;
        fileSize: number;
        fileExtension: string;
    }) => void;

    setColumns: (columns: string[], suggestedTarget: string) => void;
    setSelectedTarget: (column: string | null) => void;
    setTargetConfirmed: (confirmed: boolean) => void;

    resetAll: () => void;
}

export const useDiagnosticsStore = create<DiagnosticsStore>((set) => ({
    // Initial state
    state: "idle",
    selectedFile: null,
    uploadedFile: null,
    validationError: null,
    analysisResult: null,
    analysisError: null,

    fileUploadStatus: "idle",
    fileName: "",
    fileSize: 0,
    fileExtension: "",

    columns: [],
    suggestedTarget: "",
    selectedTarget: null,
    targetConfirmed: false,

    // Actions
    setState: (state) => set({ state }),
    setSelectedFile: (selectedFile) => set({ selectedFile }),
    setUploadedFile: (uploadedFile) => set({ uploadedFile }),
    setValidationError: (validationError) => set({ validationError }),
    setAnalysisResult: (analysisResult) => set({ analysisResult }),
    setAnalysisError: (error) => set({ analysisError: error }),

    setFileUploadInfo: (info) =>
        set({
            fileUploadStatus: info.status,
            fileName: info.fileName,
            fileSize: info.fileSize,
            fileExtension: info.fileExtension,
        }),

    setColumns: (columns, suggestedTarget) =>
        set({ columns, suggestedTarget }),

    setSelectedTarget: (selectedTarget) => set({ selectedTarget }),
    setTargetConfirmed: (targetConfirmed) => set({ targetConfirmed }),

    resetAll: () =>
        set({
            state: "idle",
            selectedFile: null,
            uploadedFile: null,
            validationError: null,
            analysisResult: null,
            analysisError: null,
            fileUploadStatus: "idle",
            fileName: "",
            fileSize: 0,
            fileExtension: "",
            columns: [],
            suggestedTarget: "",
            selectedTarget: null,
            targetConfirmed: false,
        }),
}));
