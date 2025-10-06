"use client";

import { useCallback, useEffect, useState } from "react";
import {
  UploadCloud,
  ImageIcon,
  FileText,
  FileJson,
  FileSpreadsheet,
  FileType,
  FileIcon,
  AlertCircle,
  Loader2,
  XCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { UploadArea } from "@/components/upload-area";
import { FileCard } from "@/components/file-card";
import { ResultsTable } from "@/components/results-table";
import { ParticlesBg } from "@/components/particles-bg";

type FileStatus =
  | "idle"
  | "uploading"
  | "uploaded"
  | "processing"
  | "done"
  | "error";
type SupportedKind =
  | "image"
  | "pdf"
  | "text"
  | "csv"
  | "xlsx"
  | "json"
  | "xml"
  | "doc";

type AnalyzedResult = {
  id: string;
  name: string;
  kind: SupportedKind;
  description: string;
  keyFindings: string[];
};

type TrackedFile = {
  id: string;
  file: File;
  name: string;
  size: number;
  kind: SupportedKind;
  uploadProgress: number;
  processingProgress: number;
  status: FileStatus;
  error?: string;
};

const ACCEPT = [
  "image/*",
  "application/pdf",
  "text/plain",
  "text/csv",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "application/vnd.ms-excel",
  "application/json",
  "application/xml",
  "application/msword",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
].join(",");

const SUPPORTED_EXTS = [
  "png",
  "jpg",
  "jpeg",
  "bmp",
  "tiff",
  "tif",
  "webp",
  "gif",
  "pdf",
  "txt",
  "csv",
  "xlsx",
  "xls",
  "json",
  "xml",
  "docx",
  "doc",
];

function uid() {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

function getExt(name: string) {
  const parts = name.toLowerCase().split(".");
  return parts.length > 1 ? parts.pop()! : "";
}

function humanSize(bytes: number) {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${
    sizes[i]
  }`;
}

function kindFromFile(file: File): SupportedKind | null {
  const ext = getExt(file.name);
  const type = file.type;
  if (type.startsWith("image/")) return "image";
  if (type === "application/pdf" || ext === "pdf") return "pdf";
  if (type === "text/plain" || ext === "txt") return "text";
  if (type === "text/csv" || ext === "csv") return "csv";
  if (type.includes("spreadsheet") || ext === "xlsx" || ext === "xls")
    return "xlsx";
  if (type === "application/json" || ext === "json") return "json";
  if (type === "application/xml" || type === "text/xml" || ext === "xml")
    return "xml";
  if (type.includes("word") || ext === "doc" || ext === "docx") return "doc";
  return null;
}

function isSupported(file: File) {
  const ext = getExt(file.name);
  if (!SUPPORTED_EXTS.includes(ext)) return false;
  return kindFromFile(file) !== null;
}

function iconForKind(kind: SupportedKind) {
  switch (kind) {
    case "image":
      return ImageIcon;
    case "pdf":
      return FileText;
    case "text":
      return FileText;
    case "csv":
      return FileSpreadsheet;
    case "xlsx":
      return FileSpreadsheet;
    case "json":
      return FileJson;
    case "xml":
      return FileType;
    case "doc":
      return FileText;
    default:
      return FileIcon;
  }
}

// API call function to analyze files with backend
async function analyzeFilesWithBackend(
  files: TrackedFile[]
): Promise<AnalyzedResult[]> {
  const formData = new FormData();

  // Add files to form data
  files.forEach((file) => {
    formData.append("files", file.file);
  });

  try {
    const response = await fetch("http://localhost:8001/analyze", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    // Helpers to sanitize AI output for UI
    const sanitizeDescription = (text: string): string => {
      if (!text) return "";
      let t = String(text).trim();
      // Remove leading "Filename" and optional (size) prefix
      t = t.replace(/^\s*\"[^\"\n]+\"\s*(\([^\)]*\))?\s*/g, "");
      return t.trim();
    };
    const sanitizeFinding = (text: string): string => {
      if (!text) return "";
      let t = String(text).trim();
      // Remove markdown bold markers
      t = t.replace(/\*\*(.*?)\*\*/g, "$1");
      // Remove leading bullets/symbols
      t = t.replace(/^[\u2022\-*]+\s*/, "");
      return t.trim();
    };

    // Convert backend response to frontend format
    return data.results.map((result: any, index: number) => {
      const file = files[index];
      return {
        id: file.id,
        name: result.fileName,
        kind: result.type.toLowerCase() as SupportedKind,
        description: sanitizeDescription(result.description),
        keyFindings: Array.isArray(result.keyFindings)
          ? result.keyFindings.map(sanitizeFinding)
          : [],
      };
    });
  } catch (error) {
    console.error("Error analyzing files:", error);
    throw new Error("Failed to analyze files with AI");
  }
}

export default function Page() {
  const [files, setFiles] = useState<TrackedFile[]>([]);
  const [errors, setErrors] = useState<string[]>([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [results, setResults] = useState<AnalyzedResult[]>([]);
  const [backendConnected, setBackendConnected] = useState<boolean | null>(
    null
  );

  // Check backend connection on mount
  useEffect(() => {
    const checkBackend = async () => {
      try {
        const response = await fetch("http://localhost:8001/");
        if (response.ok) {
          setBackendConnected(true);
        } else {
          setBackendConnected(false);
        }
      } catch (error) {
        setBackendConnected(false);
        console.warn("Backend not available:", error);
      }
    };
    checkBackend();
  }, []);

  const onFilesSelected = useCallback((incoming: File[]) => {
    const newErrors: string[] = [];
    const toAdd: TrackedFile[] = [];

    incoming.forEach((file) => {
      if (!isSupported(file)) {
        newErrors.push(`Unsupported file: ${file.name}`);
        return;
      }
      const kind = kindFromFile(file)!;
      const id = uid();
      toAdd.push({
        id,
        file,
        name: file.name,
        size: file.size,
        kind,
        uploadProgress: 0,
        processingProgress: 0,
        status: "uploading",
      });
    });

    if (newErrors.length) setErrors((prev) => [...prev, ...newErrors]);
    if (!toAdd.length) return;

    setFiles((prev) => [...prev, ...toAdd]);

    // Simulate upload progress
    toAdd.forEach((tf) => {
      const step = () => {
        setFiles((prev) =>
          prev.map((f) => {
            if (f.id !== tf.id) return f;
            const inc = Math.floor(10 + Math.random() * 20);
            const next = Math.min(100, f.uploadProgress + inc);
            return {
              ...f,
              uploadProgress: next,
              status: next === 100 ? "uploaded" : "uploading",
            };
          })
        );
        if (tf.uploadProgress < 100) {
          setTimeout(step, 150 + Math.random() * 200);
        }
      };
      setTimeout(step, 250);
    });
  }, []);

  const hasFiles = files.length > 0;
  const canAnalyze =
    hasFiles &&
    files.some((f) => f.status === "uploaded" || f.status === "done");

  const analyze = async () => {
    setAnalyzing(true);
    setResults([]);

    // Get files ready for analysis
    const filesToAnalyze = files.filter(
      (f) => f.status === "uploaded" || f.status === "done"
    );

    // Set all files to processing status
    setFiles((prev) =>
      prev.map((f) =>
        filesToAnalyze.some((fta) => fta.id === f.id)
          ? { ...f, status: "processing" as FileStatus, processingProgress: 0 }
          : f
      )
    );

    // Simulate progress for visual feedback
    const progressInterval = setInterval(() => {
      setFiles((prev) =>
        prev.map((f) => {
          if (f.status === "processing" && f.processingProgress < 90) {
            const increment = Math.floor(5 + Math.random() * 10);
            return {
              ...f,
              processingProgress: Math.min(
                90,
                f.processingProgress + increment
              ),
            };
          }
          return f;
        })
      );
    }, 200);

    try {
      // Call the backend API
      const analysisResults = await analyzeFilesWithBackend(filesToAnalyze);

      // Update results
      setResults(analysisResults);

      // Set all files to done status
      setFiles((prev) =>
        prev.map((f) =>
          filesToAnalyze.some((fta) => fta.id === f.id)
            ? { ...f, status: "done" as FileStatus, processingProgress: 100 }
            : f
        )
      );
    } catch (error) {
      console.error("Analysis failed:", error);

      // Add error to errors list
      setErrors((prev) => [
        ...prev,
        `Analysis failed: ${
          error instanceof Error ? error.message : "Unknown error"
        }`,
      ]);

      // Set files back to uploaded status on error
      setFiles((prev) =>
        prev.map((f) =>
          filesToAnalyze.some((fta) => fta.id === f.id)
            ? { ...f, status: "uploaded" as FileStatus, processingProgress: 0 }
            : f
        )
      );
    } finally {
      clearInterval(progressInterval);
      setAnalyzing(false);
    }
  };

  const dismissError = (i: number) => {
    setErrors((prev) => prev.filter((_, idx) => idx !== i));
  };

  const clearAll = () => {
    setFiles([]);
    setResults([]);
    setErrors([]);
    setAnalyzing(false);
  };

  return (
    <main className="relative min-h-screen bg-background text-foreground overflow-hidden">
      <ParticlesBg />

      <div className="relative mx-auto max-w-6xl px-4 py-10 md:py-14">
        <header className="mb-8 md:mb-12">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-pretty text-3xl md:text-4xl font-semibold tracking-tight">
                AI File Analyzer
              </h1>
            </div>
            {/* Backend Status Indicator */}
            <div className="flex items-center gap-2">
              <div
                className={`w-2 h-2 rounded-full ${
                  backendConnected === null
                    ? "bg-yellow-500 animate-pulse"
                    : backendConnected
                    ? "bg-green-500"
                    : "bg-red-500"
                }`}
              />
              <span className="text-xs text-muted-foreground">
                {backendConnected === null
                  ? "Checking backend..."
                  : backendConnected
                  ? "AI Backend Connected"
                  : "Backend Offline"}
              </span>
            </div>
          </div>
        </header>

        {/* Errors */}
        {errors.length > 0 && (
          <div className="mb-6 space-y-2">
            {errors.map((e, i) => (
              <div
                key={i}
                className="flex items-start gap-2 rounded-lg border border-border/60 bg-accent/5 px-3 py-2 animate-in fade-in zoom-in duration-300"
              >
                <AlertCircle className="h-5 w-5 text-destructive" aria-hidden />
                <div className="flex-1 text-sm">{e}</div>
                <button
                  onClick={() => dismissError(i)}
                  className="text-muted-foreground hover:text-foreground transition-colors"
                  aria-label="Dismiss error"
                >
                  <XCircle className="h-5 w-5" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Upload Area */}
        <section className="mb-8 md:mb-10">
          <UploadArea
            accept={ACCEPT}
            onSelect={onFilesSelected}
            className="rounded-xl"
          />
        </section>

        {/* Files Grid */}
        {hasFiles && (
          <section className="mb-8 md:mb-10">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-lg font-medium">Uploaded Files</h2>
              <div className="flex items-center gap-2">
                <button
                  onClick={analyze}
                  disabled={!canAnalyze || analyzing || !backendConnected}
                  className={cn(
                    "inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-primary-foreground transition-all",
                    "hover:translate-y-[1px] hover:shadow-[0_0_0_3px_var(--color-primary)/20]",
                    "disabled:opacity-60 disabled:hover:translate-y-0 disabled:cursor-not-allowed cursor-pointer",
                    !backendConnected && "bg-red-500 hover:bg-red-600"
                  )}
                >
                  {analyzing ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Analyzing...
                    </>
                  ) : !backendConnected ? (
                    <>
                      <AlertCircle className="h-4 w-4" />
                      Backend Offline
                    </>
                  ) : (
                    <>
                      <UploadCloud className="h-4 w-4" />
                      Analyze Files
                    </>
                  )}
                </button>
                <button
                  onClick={clearAll}
                  className="rounded-lg border border-border px-3 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-accent/10 transition-colors"
                >
                  Clear
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {files.map((f, idx) => (
                <FileCard
                  key={f.id}
                  index={idx}
                  name={f.name}
                  sizeLabel={humanSize(f.size)}
                  kind={f.kind}
                  status={f.status}
                  uploadProgress={f.uploadProgress}
                  processingProgress={f.processingProgress}
                  Icon={iconForKind(f.kind)}
                />
              ))}
            </div>
          </section>
        )}

        {/* Results */}
        {hasFiles && (
          <section className="mb-16">
            <h2 className="mb-3 text-lg font-medium">Results</h2>
            <ResultsTable
              results={results}
              isProcessing={
                analyzing || files.some((f) => f.status === "processing")
              }
            />
          </section>
        )}
      </div>
    </main>
  );
}
