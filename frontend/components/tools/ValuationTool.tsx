"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useValuation } from "@/lib/hooks/useTools";
import { DollarSign, TrendingUp, AlertTriangle } from "lucide-react";

function formatCurrency(value: number): string {
  if (value >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(1)}B`;
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`;
  return `$${value.toFixed(0)}`;
}

export function ValuationTool() {
  const [revenue, setRevenue] = useState("");
  const [growthRate, setGrowthRate] = useState("");
  const [industry, setIndustry] = useState("");
  const mutation = useValuation();

  const handleSubmit = () => {
    mutation.mutate({
      revenue: revenue ? Number(revenue) : null,
      growth_rate: growthRate ? Number(growthRate) / 100 : null,
      industry: industry || null,
    });
  };

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="space-y-2">
          <Label htmlFor="revenue">Annual Revenue ($)</Label>
          <Input
            id="revenue"
            type="number"
            placeholder="1000000"
            value={revenue}
            onChange={(e) => setRevenue(e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="growth">Growth Rate (%)</Label>
          <Input
            id="growth"
            type="number"
            placeholder="100"
            value={growthRate}
            onChange={(e) => setGrowthRate(e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="industry">Industry</Label>
          <Input
            id="industry"
            placeholder="saas, fintech, etc."
            value={industry}
            onChange={(e) => setIndustry(e.target.value)}
          />
        </div>
      </div>

      <Button onClick={handleSubmit} disabled={mutation.isPending}>
        {mutation.isPending ? "Computing..." : "Calculate Valuation"}
      </Button>

      {mutation.data && (
        <div className="space-y-4">
          {/* Summary range */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm">
                <DollarSign className="h-4 w-4" />
                Estimated Valuation Range
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-baseline gap-2">
                <span className="text-sm text-muted-foreground">
                  {formatCurrency(mutation.data.summary.low)}
                </span>
                <span className="text-2xl font-bold">
                  {formatCurrency(mutation.data.summary.mid)}
                </span>
                <span className="text-sm text-muted-foreground">
                  {formatCurrency(mutation.data.summary.high)}
                </span>
              </div>
            </CardContent>
          </Card>

          {/* Method breakdown */}
          <div className="grid gap-4 sm:grid-cols-3">
            {mutation.data.methods.map((method) => (
              <Card key={method.method}>
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center gap-2 text-sm">
                    <TrendingUp className="h-4 w-4" />
                    {method.method.replace(/_/g, " ")}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="text-lg font-semibold">
                    {formatCurrency(method.mid)}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {formatCurrency(method.low)} — {formatCurrency(method.high)}
                  </div>
                  <ul className="space-y-1">
                    {method.assumptions.map((a, i) => (
                      <li key={i} className="text-xs text-muted-foreground">
                        {a}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Warnings */}
          {mutation.data.warnings.length > 0 && (
            <div className="flex items-start gap-2 rounded-lg border border-yellow-200 bg-yellow-50 p-3 dark:border-yellow-900 dark:bg-yellow-950">
              <AlertTriangle className="h-4 w-4 text-yellow-600 mt-0.5" />
              <ul className="space-y-1 text-sm text-yellow-700 dark:text-yellow-400">
                {mutation.data.warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
