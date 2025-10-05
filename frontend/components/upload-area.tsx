"use client";

import type React from "react";
import { useCallback, useRef, useState } from "react";
import { UploadCloud } from "lucide-react";
import { cn } from "@/lib/utils";

export function UploadArea({
  onSelect,
  accept,
  className,
}: {
  onSelect: (files: File[]) => void;
  accept?: string;
  className?: string;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [loadingClick, setLoadingClick] = useState(false);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragging(false);
      const files = Array.from(e.dataTransfer.files || []);
      if (files.length) onSelect(files);
    },
    [onSelect]
  );

  const onBrowse = () => {
    setLoadingClick(true);
    setTimeout(() => setLoadingClick(false), 500);
    inputRef.current?.click();
  };

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
      className={cn(
        "relative w-full border-2 border-dashed border-border/60 px-5 py-10",
        "transition-all duration-300",
        "hover:border-primary/60 hover:bg-accent/5",
        dragging &&
          "border-primary bg-accent/10 shadow-[0_0_0_3px_var(--color-primary)/15]",
        "animate-in fade-in duration-500",
        className
      )}
      aria-label="File upload area"
    >
      {/* pulsing glow ring */}
      <div
        className={cn(
          "pointer-events-none absolute inset-0 rounded-xl",
          dragging ? "ring-2 ring-primary animate-pulse" : "ring-0"
        )}
      />

      <div className="relative z-10 mx-auto max-w-xl text-center">
        <UploadCloud
          className="mx-auto mb-3 h-8 w-8 text-primary"
          aria-hidden
        />
        <p className="text-sm text-muted-foreground">
          Drag and drop your files here, or
        </p>
        <div className="mt-3">
          <button
            type="button"
            onClick={onBrowse}
            className={cn(
              "inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-primary-foreground",
              "transition-all duration-200 hover:translate-y-[1px] cursor-pointer hover:shadow-[0_0_0_3px_var(--color-primary)/20]",
              loadingClick && "opacity-80"
            )}
          >
            {loadingClick ? (
              <>
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-primary-foreground/40 border-t-transparent" />
                Choosing...
              </>
            ) : (
              <>
                <UploadCloud className="h-4 w-4" />
                Choose files
              </>
            )}
          </button>
        </div>
        <p className="mt-2 text-xs text-muted-foreground">
          Supported: PNG, JPG, JPEG, BMP, TIFF, TIF, WebP, GIF, PDF, TXT, CSV,
          XLSX, XLS, JSON, XML, DOCX, DOC
        </p>
      </div>

      <input
        ref={inputRef}
        type="file"
        className="sr-only"
        multiple
        accept={accept}
        onChange={(e) => {
          const files = Array.from(e.target.files || []);
          if (files.length) onSelect(files);
          e.currentTarget.value = "";
        }}
      />
    </div>
  );
}
