"use client";

import { BarChart3 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getConfidenceColor } from "@/lib/utils/confidenceColor";
import type { EntityResult } from "@/lib/types";

interface MetricsOverviewProps {
  metrics: EntityResult[];
}

export function MetricsOverview({ metrics }: MetricsOverviewProps) {
  if (metrics.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
        <BarChart3 className="mb-2 h-8 w-8" />
        <p className="text-sm">No metrics extracted yet.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {metrics.map((metric) => {
        const name =
          (metric.data.name as string) ??
          (metric.data.metric_name as string) ??
          "Metric";
        const value = metric.data.value ?? metric.data.current_value ?? "—";
        const unit = metric.data.unit as string | undefined;

        return (
          <Card key={metric.id}>
            <CardHeader className="pb-1">
              <CardTitle className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                <div
                  className={`h-2 w-2 rounded-full ${getConfidenceColor(metric.confidence)}`}
                />
                {name}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xl font-bold">
                {String(value)}
                {unit && (
                  <span className="ml-1 text-sm font-normal text-muted-foreground">
                    {unit}
                  </span>
                )}
              </p>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
