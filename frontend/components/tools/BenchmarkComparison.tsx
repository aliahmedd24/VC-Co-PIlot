"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PercentileBar } from "@/components/charts/PercentileBar";
import { useBenchmarks } from "@/lib/hooks/useTools";
import { BarChart3, TrendingUp, TrendingDown } from "lucide-react";

export function BenchmarkComparison() {
  const [industry, setIndustry] = useState("saas");
  const [stage, setStage] = useState("seed");
  const [mrrGrowth, setMrrGrowth] = useState("");
  const [grossMargin, setGrossMargin] = useState("");
  const [burnRate, setBurnRate] = useState("");
  const mutation = useBenchmarks();

  const handleSubmit = () => {
    const metrics: Record<string, number> = {};
    if (mrrGrowth) metrics.mrr_growth = Number(mrrGrowth);
    if (grossMargin) metrics.gross_margin = Number(grossMargin);
    if (burnRate) metrics.burn_rate = Number(burnRate);

    mutation.mutate({ industry, stage, metrics });
  };

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <div className="space-y-2">
          <Label>Industry</Label>
          <Input value={industry} onChange={(e) => setIndustry(e.target.value)} />
        </div>
        <div className="space-y-2">
          <Label>Stage</Label>
          <Input value={stage} onChange={(e) => setStage(e.target.value)} />
        </div>
        <div className="space-y-2">
          <Label>MRR Growth (%)</Label>
          <Input type="number" value={mrrGrowth} onChange={(e) => setMrrGrowth(e.target.value)} />
        </div>
        <div className="space-y-2">
          <Label>Gross Margin (%)</Label>
          <Input type="number" value={grossMargin} onChange={(e) => setGrossMargin(e.target.value)} />
        </div>
        <div className="space-y-2">
          <Label>Burn Rate ($K/mo)</Label>
          <Input type="number" value={burnRate} onChange={(e) => setBurnRate(e.target.value)} />
        </div>
      </div>

      <Button onClick={handleSubmit} disabled={mutation.isPending}>
        {mutation.isPending ? "Analyzing..." : "Compare Benchmarks"}
      </Button>

      {mutation.data && (
        <div className="space-y-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm">
                <BarChart3 className="h-4 w-4" />
                Benchmark Results — {mutation.data.industry} / {mutation.data.stage}
                <span className="text-muted-foreground font-normal">
                  ({mutation.data.cohort_size} peers)
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {mutation.data.metrics.map((m) => (
                <PercentileBar
                  key={m.name}
                  label={m.name.replace(/_/g, " ")}
                  percentile={m.percentile}
                  p25={m.p25}
                  median={m.median}
                  p75={m.p75}
                  value={m.value}
                  classification={m.classification}
                />
              ))}
            </CardContent>
          </Card>

          <div className="grid gap-4 sm:grid-cols-2">
            {mutation.data.strengths.length > 0 && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center gap-2 text-sm text-green-600">
                    <TrendingUp className="h-4 w-4" />
                    Strengths
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-1">
                    {mutation.data.strengths.map((s, i) => (
                      <li key={i} className="text-sm">{s}</li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}

            {mutation.data.weaknesses.length > 0 && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center gap-2 text-sm text-red-600">
                    <TrendingDown className="h-4 w-4" />
                    Areas to Improve
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-1">
                    {mutation.data.weaknesses.map((w, i) => (
                      <li key={i} className="text-sm">{w}</li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
