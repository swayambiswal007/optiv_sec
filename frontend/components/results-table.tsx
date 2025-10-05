"use client";

import type React from "react";
import { cn } from "@/lib/utils";

type SupportedKind =
  | "image"
  | "pdf"
  | "text"
  | "csv"
  | "xlsx"
  | "json"
  | "xml"
  | "doc";
type Result = {
  id: string;
  name: string;
  kind: SupportedKind;
  description: string;
  keyFindings: string[];
};

export function ResultsTable({
  results,
  isProcessing,
}: {
  results: Result[];
  isProcessing: boolean;
}) {
  const showSkeletons = isProcessing && results.length === 0;

  return (
    <div className="overflow-hidden rounded-lg border border-border/60 bg-black">
      <div className="grid grid-cols-12 border-b border-border/60 bg-accent/5 px-3 py-2 text-xs uppercase tracking-wide text-muted-foreground">
        <div className="col-span-4">File Name</div>
        <div className="col-span-2">Type</div>
        <div className="col-span-3">Description</div>
        <div className="col-span-3">Key Findings</div>
      </div>

      <div className="divide-y divide-border/60">
        {results.map((r, idx) => (
          <div
            key={r.id}
            className={cn(
              "grid grid-cols-12 items-start px-3 py-3 transition",
              "hover:bg-accent/5 hover:shadow-[0_0_24px_rgba(6,182,212,0.10)]"
            )}
            style={{ animationDelay: `${idx * 40}ms` } as React.CSSProperties}
          >
            <div className="col-span-4 truncate pr-2">{r.name}</div>
            <div className="col-span-2 pr-2 uppercase text-xs text-muted-foreground">
              {r.kind}
            </div>
            <div className="col-span-3 pr-3 text-sm text-pretty">
              {r.description}
            </div>
            <div className="col-span-3">
              <ul className="list-disc pl-5 text-sm">
                {r.keyFindings.map((k, i) => (
                  <li key={i} className="marker:text-primary">
                    {k}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ))}

        {showSkeletons &&
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="grid grid-cols-12 items-start px-3 py-3">
              <div className="col-span-4 pr-2">
                <div className="h-4 w-2/3 animate-pulse rounded bg-accent/10" />
              </div>
              <div className="col-span-2 pr-2">
                <div className="h-4 w-12 animate-pulse rounded bg-accent/10" />
              </div>
              <div className="col-span-3 pr-3">
                <div className="h-4 w-11/12 animate-pulse rounded bg-accent/10" />
              </div>
              <div className="col-span-3">
                <div className="mb-1 h-4 w-10/12 animate-pulse rounded bg-accent/10" />
                <div className="h-4 w-8/12 animate-pulse rounded bg-accent/10" />
              </div>
            </div>
          ))}

        {!isProcessing && results.length === 0 && (
          <div className="px-3 py-6 text-center text-sm text-muted-foreground">
            No results yet. Upload files and click Analyze.
          </div>
        )}
      </div>
    </div>
  );
}
