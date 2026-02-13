"use client";

import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface KPIMetric {
  name?: string;
  value?: number | string;
  unit?: string;
  target?: number | string;
  trend?: "up" | "down" | "flat";
  period?: string;
}

interface KPIDashboardContent {
  title?: string;
  metrics?: KPIMetric[];
  summary?: string;
}

interface KPIDashboardRendererProps {
  content: Record<string, unknown>;
}

function TrendIcon({ trend }: { trend?: string }) {
  if (trend === "up")
    return <TrendingUp className="h-4 w-4 text-green-600" />;
  if (trend === "down")
    return <TrendingDown className="h-4 w-4 text-red-600" />;
  return <Minus className="h-4 w-4 text-muted-foreground" />;
}

export function KPIDashboardRenderer({ content }: KPIDashboardRendererProps) {
  const c = content as KPIDashboardContent;
  const metrics = c.metrics ?? [];

  return (
    <div data-testid="kpi-dashboard" className="space-y-4">
      {c.title && <h3 className="text-lg font-semibold">{c.title}</h3>}
      {c.summary && (
        <p className="text-sm text-muted-foreground">{c.summary}</p>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {metrics.map((metric, i) => (
          <Card key={i}>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center justify-between text-sm font-medium text-muted-foreground">
                <span>{metric.name ?? `Metric ${i + 1}`}</span>
                <TrendIcon trend={metric.trend} />
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {String(metric.value ?? "—")}
                {metric.unit && (
                  <span className="ml-1 text-sm font-normal text-muted-foreground">
                    {metric.unit}
                  </span>
                )}
              </div>
              {metric.target !== undefined && (
                <p className="mt-1 text-xs text-muted-foreground">
                  Target: {String(metric.target)}
                  {metric.unit ? ` ${metric.unit}` : ""}
                </p>
              )}
              {metric.period && (
                <p className="text-xs text-muted-foreground">
                  {metric.period}
                </p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {metrics.length === 0 && (
        <p className="text-sm text-muted-foreground italic">
          No metrics defined yet.
        </p>
      )}
    </div>
  );
}
