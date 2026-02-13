"use client";

import { cn } from "@/lib/utils/cn";

interface PercentileBarProps {
  label: string;
  percentile: number;
  p25: number;
  median: number;
  p75: number;
  value: number;
  classification: string;
}

export function PercentileBar({
  label,
  percentile,
  classification,
}: PercentileBarProps) {
  const classColor =
    classification === "strong"
      ? "bg-green-500"
      : classification === "weak"
        ? "bg-red-500"
        : "bg-yellow-500";

  return (
    <div data-testid="percentile-bar" className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium">{label}</span>
        <span
          className={cn(
            "rounded px-2 py-0.5 text-xs font-medium text-white",
            classColor
          )}
        >
          P{Math.round(percentile)} — {classification}
        </span>
      </div>
      <div className="relative h-3 w-full rounded-full bg-muted">
        {/* Quartile markers */}
        <div className="absolute left-1/4 top-0 h-full w-px bg-border" />
        <div className="absolute left-1/2 top-0 h-full w-px bg-border" />
        <div className="absolute left-3/4 top-0 h-full w-px bg-border" />
        {/* Value indicator */}
        <div
          className={cn("absolute top-0 h-full rounded-full", classColor)}
          style={{ width: `${Math.min(percentile, 100)}%` }}
        />
      </div>
      <div className="flex justify-between text-[10px] text-muted-foreground">
        <span>0</span>
        <span>25th</span>
        <span>50th</span>
        <span>75th</span>
        <span>100th</span>
      </div>
    </div>
  );
}
