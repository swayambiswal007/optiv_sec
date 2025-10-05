"use client";

import type React from "react";
import { cn } from "@/lib/utils";
import Image from "next/image";

type Props = {
  index: number;
  name: string;
  sizeLabel: string;
  kind: "image" | "pdf" | "text" | "csv" | "xlsx" | "json" | "xml" | "doc";
  status: "idle" | "uploading" | "uploaded" | "processing" | "done" | "error";
  uploadProgress: number;
  processingProgress: number;
  previewUrl?: string;
  Icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
};

export function FileCard({
  index,
  name,
  sizeLabel,
  kind,
  status,
  uploadProgress,
  processingProgress,
  previewUrl,
  Icon,
}: Props) {
  const showThumb = kind === "image" && previewUrl;

  return (
    <div
      className={cn(
        "group relative overflow-hidden rounded-xl border border-border/60 bg-black backdrop-blur-sm p-5",
        "transition-all duration-300 hover:border-primary/60 hover:shadow-[0_0_32px_rgba(6,182,212,0.25)]",
        "animate-in fade-in slide-in-from-bottom-2"
      )}
      style={{ animationDelay: `${index * 40}ms` } as React.CSSProperties}
    >
      {/* Header */}
      <div className="flex items-center gap-4">
        <div
          className={cn(
            "flex h-14 w-14 items-center justify-center rounded-lg border border-border/60 bg-accent/5 shadow-inner",
            "transition-colors group-hover:bg-accent/10"
          )}
        >
          {showThumb ? (
            <Image
              src={previewUrl! || "/placeholder.svg"}
              alt=""
              width={56}
              height={56}
              className="h-14 w-14 rounded-md object-cover"
            />
          ) : (
            <Icon className="h-6 w-6 text-primary" aria-hidden />
          )}
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="truncate text-sm font-medium text-foreground/90">
              {name}
            </p>
            <span className="rounded-md border border-border/60 bg-accent/10 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-muted-foreground">
              {kind}
            </span>
          </div>
          <p className="mt-0.5 text-xs text-muted-foreground/80">{sizeLabel}</p>
        </div>

        <div className="absolute right-4 top-4">
          <StatusPill status={status} />
        </div>
      </div>

      {/* Progress Section */}
      <div className="mt-4 space-y-2">
        <ProgressBar
          label={status === "uploading" ? "Uploading" : "Upload"}
          value={uploadProgress}
          success={uploadProgress === 100}
        />
        <ProgressBar
          label="Processing"
          value={processingProgress}
          success={status === "done"}
        />
      </div>
    </div>
  );
}

function ProgressBar({
  label,
  value,
  success,
}: {
  label: string;
  value: number;
  success?: boolean;
}) {
  return (
    <div className="w-full">
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground">{label}</span>
        <span className="text-xs tabular-nums text-muted-foreground">
          {value}%
        </span>
      </div>
      <div className="mt-1 h-2 w-full overflow-hidden rounded bg-accent/10">
        <div
          className={cn(
            "h-full rounded bg-primary transition-all duration-300",
            success && "bg-success"
          )}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
}

function StatusPill({
  status,
}: {
  status: "idle" | "uploading" | "uploaded" | "processing" | "done" | "error";
}) {
  if (status === "done") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-success/15 px-2 py-1 text-[10px] text-success">
        <svg className="h-3 w-3" viewBox="0 0 24 24" fill="none" aria-hidden>
          <path
            d="M20 7 9 18l-5-5"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        Done
      </span>
    );
  }
  if (status === "processing") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-primary/15 px-2 py-1 text-[10px] text-primary">
        <span className="h-3 w-3 animate-spin rounded-full border-2 border-primary/50 border-t-transparent" />
        Processing
      </span>
    );
  }
  if (status === "uploading") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-accent/15 px-2 py-1 text-[10px] text-muted-foreground">
        <span className="h-3 w-3 animate-pulse rounded-full bg-primary/70" />
        Uploading
      </span>
    );
  }
  if (status === "uploaded") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-accent/15 px-2 py-1 text-[10px] text-muted-foreground">
        Ready
      </span>
    );
  }
  if (status === "error") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-destructive/15 px-2 py-1 text-[10px] text-destructive">
        Error
      </span>
    );
  }
  return null;
}
