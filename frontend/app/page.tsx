"use client"

import { useCallback, useEffect, useState } from "react"
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
} from "lucide-react"
import { cn } from "@/lib/utils"
import { UploadArea } from "@/components/upload-area"
import { FileCard } from "@/components/file-card"
import { ResultsTable } from "@/components/results-table"
import { ParticlesBg } from "@/components/particles-bg"

type FileStatus = "idle" | "uploading" | "uploaded" | "processing" | "done" | "error"
type SupportedKind = "image" | "pdf" | "text" | "csv" | "xlsx" | "json" | "xml" | "doc"

type AnalyzedResult = {
  id: string
  name: string
  kind: SupportedKind
  description: string
  keyFindings: string[]
}

type TrackedFile = {
  id: string
  file: File
  name: string
  size: number
  kind: SupportedKind
  previewUrl?: string
  uploadProgress: number
  processingProgress: number
  status: FileStatus
  error?: string
}

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
].join(",")

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
]

function uid() {
  return Math.random().toString(36).slice(2) + Date.now().toString(36)
}

function getExt(name: string) {
  const parts = name.toLowerCase().split(".")
  return parts.length > 1 ? parts.pop()! : ""
}

function humanSize(bytes: number) {
  if (bytes === 0) return "0 B"
  const k = 1024
  const sizes = ["B", "KB", "MB", "GB"]
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`
}

function kindFromFile(file: File): SupportedKind | null {
  const ext = getExt(file.name)
  const type = file.type
  if (type.startsWith("image/")) return "image"
  if (type === "application/pdf" || ext === "pdf") return "pdf"
  if (type === "text/plain" || ext === "txt") return "text"
  if (type === "text/csv" || ext === "csv") return "csv"
  if (type.includes("spreadsheet") || ext === "xlsx" || ext === "xls") return "xlsx"
  if (type === "application/json" || ext === "json") return "json"
  if (type === "application/xml" || type === "text/xml" || ext === "xml") return "xml"
  if (type.includes("word") || ext === "doc" || ext === "docx") return "doc"
  return null
}

function isSupported(file: File) {
  const ext = getExt(file.name)
  if (!SUPPORTED_EXTS.includes(ext)) return false
  return kindFromFile(file) !== null
}

function iconForKind(kind: SupportedKind) {
  switch (kind) {
    case "image":
      return ImageIcon
    case "pdf":
      return FileText
    case "text":
      return FileText
    case "csv":
      return FileSpreadsheet
    case "xlsx":
      return FileSpreadsheet
    case "json":
      return FileJson
    case "xml":
      return FileType
    case "doc":
      return FileText
    default:
      return FileIcon
  }
}

function mockDescribe(kind: SupportedKind, name: string, size: number) {
  const base = `“${name}” (${humanSize(size)})`
  switch (kind) {
    case "image":
      return `${base} appears to be an image; analysis infers key subjects, color palette, and possible context.`
    case "pdf":
      return `${base} is a PDF document; likely contains formatted text with potential images or tables.`
    case "text":
      return `${base} is a plain text file; content is likely unstructured notes or logs.`
    case "csv":
      return `${base} is a CSV dataset; tabular structure with delimited fields.`
    case "xlsx":
      return `${base} is a spreadsheet; multiple sheets and formatted cells are possible.`
    case "json":
      return `${base} is a JSON file; hierarchical key-value data structure detected.`
    case "xml":
      return `${base} is an XML file; structured markup with tags and attributes.`
    case "doc":
      return `${base} is a Word document; styled text and embedded media possible.`
  }
}

function mockFindings(kind: SupportedKind) {
  switch (kind) {
    case "image":
      return ["Detected dominant colors", "Potential subjects identified", "EXIF-like metadata (mocked)"]
    case "pdf":
      return ["Headings and sections parsed", "Text blocks extracted", "Embedded image detection"]
    case "text":
      return ["Language detected", "Keyword frequency approx.", "Potential TODOs or dates"]
    case "csv":
      return ["Column names recognized", "Missing values estimation", "Outlier detection (mocked)"]
    case "xlsx":
      return ["Multiple sheets scan (mocked)", "Cell types inferred", "Basic summary stats"]
    case "json":
      return ["Keys and nesting depth", "Array lengths sampled", "Schema-like shape (mocked)"]
    case "xml":
      return ["Root tag identified", "Namespaces (if any)", "Node counts by tag"]
    case "doc":
      return ["Headings styled", "Tables/images check", "Word count approx."]
  }
}

export default function Page() {
  const [files, setFiles] = useState<TrackedFile[]>([])
  const [errors, setErrors] = useState<string[]>([])
  const [analyzing, setAnalyzing] = useState(false)
  const [results, setResults] = useState<AnalyzedResult[]>([])

  // cleanup object URLs
  useEffect(() => {
    return () => {
      files.forEach((f) => f.previewUrl && URL.revokeObjectURL(f.previewUrl))
    }
  }, [files])

  const onFilesSelected = useCallback((incoming: File[]) => {
    const newErrors: string[] = []
    const toAdd: TrackedFile[] = []

    incoming.forEach((file) => {
      if (!isSupported(file)) {
        newErrors.push(`Unsupported file: ${file.name}`)
        return
      }
      const kind = kindFromFile(file)!
      const id = uid()
      const previewUrl = kind === "image" ? URL.createObjectURL(file) : undefined
      toAdd.push({
        id,
        file,
        name: file.name,
        size: file.size,
        kind,
        previewUrl,
        uploadProgress: 0,
        processingProgress: 0,
        status: "uploading",
      })
    })

    if (newErrors.length) setErrors((prev) => [...prev, ...newErrors])
    if (!toAdd.length) return

    setFiles((prev) => [...prev, ...toAdd])

    // Simulate upload progress
    toAdd.forEach((tf) => {
      const step = () => {
        setFiles((prev) =>
          prev.map((f) => {
            if (f.id !== tf.id) return f
            const inc = Math.floor(10 + Math.random() * 20)
            const next = Math.min(100, f.uploadProgress + inc)
            return { ...f, uploadProgress: next, status: next === 100 ? "uploaded" : "uploading" }
          }),
        )
        if (tf.uploadProgress < 100) {
          setTimeout(step, 150 + Math.random() * 200)
        }
      }
      setTimeout(step, 250)
    })
  }, [])

  const hasFiles = files.length > 0
  const canAnalyze = hasFiles && files.some((f) => f.status === "uploaded" || f.status === "done")

  const analyze = async () => {
    setAnalyzing(true)
    setResults([])

    // sequential-ish processing with per-file progress bars
    const processOne = (f: TrackedFile, idx: number) =>
      new Promise<void>((resolve) => {
        // progress ticker
        let progress = 0
        const tick = () => {
          progress = Math.min(100, progress + Math.floor(10 + Math.random() * 15))
          setFiles((prev) =>
            prev.map((x) => (x.id === f.id ? { ...x, processingProgress: progress, status: "processing" } : x)),
          )
          if (progress < 100) {
            setTimeout(tick, 180 + Math.random() * 220)
          }
        }
        setTimeout(tick, 150)

        // mock "AI" delay and result
        const totalDelay = 1000 + Math.random() * 1500 + idx * 200
        setTimeout(() => {
          const description = mockDescribe(f.kind, f.name, f.size)
          const keyFindings = mockFindings(f.kind)
          setResults((prev) => [
            ...prev,
            {
              id: f.id,
              name: f.name,
              kind: f.kind,
              description,
              keyFindings,
            },
          ])
          setFiles((prev) => prev.map((x) => (x.id === f.id ? { ...x, processingProgress: 100, status: "done" } : x)))
          resolve()
        }, totalDelay)
      })

    for (let i = 0; i < files.length; i++) {
      const f = files[i]
      if (f.status === "uploaded" || f.status === "done") {
        await processOne(f, i)
      }
    }
    setAnalyzing(false)
  }

  const dismissError = (i: number) => {
    setErrors((prev) => prev.filter((_, idx) => idx !== i))
  }

  const clearAll = () => {
    setFiles((prev) => {
      prev.forEach((f) => f.previewUrl && URL.revokeObjectURL(f.previewUrl))
      return []
    })
    setResults([])
    setErrors([])
    setAnalyzing(false)
  }

  return (
    <main className="relative min-h-screen bg-background text-foreground overflow-hidden">
      <ParticlesBg />

      <div className="relative mx-auto max-w-6xl px-4 py-10 md:py-14">
        <header className="mb-8 md:mb-12">
          <h1 className="text-pretty text-3xl md:text-4xl font-semibold tracking-tight">AI File Analyzer</h1>
          <p className="text-pretty mt-2 text-sm md:text-base text-muted-foreground">
            Upload files, then analyze them with smooth, modern animations.
          </p>
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
          <UploadArea accept={ACCEPT} onSelect={onFilesSelected} className="rounded-xl" />
        </section>

        {/* Files Grid */}
        {hasFiles && (
          <section className="mb-8 md:mb-10">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-lg font-medium">Uploaded Files</h2>
              <div className="flex items-center gap-2">
                <button
                  onClick={analyze}
                  disabled={!canAnalyze || analyzing}
                  className={cn(
                    "inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-primary-foreground transition-all",
                    "hover:translate-y-[1px] hover:shadow-[0_0_0_3px_var(--color-primary)/20]",
                    "disabled:opacity-60 disabled:hover:translate-y-0 disabled:cursor-not-allowed",
                  )}
                >
                  {analyzing ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Analyzing...
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
                  previewUrl={f.previewUrl}
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
            <ResultsTable results={results} isProcessing={analyzing || files.some((f) => f.status === "processing")} />
          </section>
        )}

        <footer className="pt-8 text-center text-xs text-muted-foreground">
          Built with smooth animations, modern UI, and pure Tailwind styling.
        </footer>
      </div>
    </main>
  )
}
