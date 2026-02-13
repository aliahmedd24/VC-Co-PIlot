"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { WaterfallChart } from "@/components/charts/WaterfallChart";
import { useScenarios } from "@/lib/hooks/useTools";
import { Plus, Trash2, DollarSign } from "lucide-react";
import type { RoundInput } from "@/lib/types";

function formatCurrency(value: number): string {
  if (value >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(1)}B`;
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`;
  return `$${value.toFixed(0)}`;
}

export function ScenarioModeler() {
  const [rounds, setRounds] = useState<RoundInput[]>([
    { raise_amount: 2000000, pre_money: 8000000, option_pool_pct: 10 },
  ]);
  const mutation = useScenarios();

  const addRound = () => {
    setRounds((prev) => [
      ...prev,
      { raise_amount: 5000000, pre_money: 20000000, option_pool_pct: 10 },
    ]);
  };

  const removeRound = (index: number) => {
    setRounds((prev) => prev.filter((_, i) => i !== index));
  };

  const updateRound = (index: number, field: keyof RoundInput, value: string) => {
    setRounds((prev) =>
      prev.map((r, i) =>
        i === index ? { ...r, [field]: Number(value) || 0 } : r
      )
    );
  };

  const handleSubmit = () => {
    mutation.mutate({ rounds, exit_multiples: [3, 5, 10, 20] });
  };

  const chartData = mutation.data?.rounds.map((r) => ({
    name: r.round_label,
    value: r.founder_ownership_pct,
  }));

  return (
    <div className="space-y-6">
      {/* Round inputs */}
      <div className="space-y-4">
        {rounds.map((round, i) => (
          <Card key={i}>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center justify-between text-sm">
                <span>Round {i + 1}</span>
                {rounds.length > 1 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeRound(i)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 sm:grid-cols-3">
                <div className="space-y-1">
                  <Label className="text-xs">Raise Amount ($)</Label>
                  <Input
                    type="number"
                    value={round.raise_amount}
                    onChange={(e) => updateRound(i, "raise_amount", e.target.value)}
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Pre-Money Valuation ($)</Label>
                  <Input
                    type="number"
                    value={round.pre_money}
                    onChange={(e) => updateRound(i, "pre_money", e.target.value)}
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Option Pool (%)</Label>
                  <Input
                    type="number"
                    value={round.option_pool_pct ?? 10}
                    onChange={(e) => updateRound(i, "option_pool_pct", e.target.value)}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}

        <div className="flex gap-2">
          <Button variant="outline" onClick={addRound}>
            <Plus className="mr-1 h-4 w-4" />
            Add Round
          </Button>
          <Button onClick={handleSubmit} disabled={mutation.isPending}>
            {mutation.isPending ? "Modeling..." : "Run Scenario"}
          </Button>
        </div>
      </div>

      {mutation.data && (
        <div className="space-y-4">
          {/* Ownership waterfall */}
          {chartData && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Founder Ownership After Each Round</CardTitle>
              </CardHeader>
              <CardContent>
                <WaterfallChart data={chartData} />
              </CardContent>
            </Card>
          )}

          {/* Cap table */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Cap Table Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-left text-muted-foreground">
                      <th className="pb-2 font-medium">Round</th>
                      <th className="pb-2 font-medium">Raise</th>
                      <th className="pb-2 font-medium">Post-Money</th>
                      <th className="pb-2 font-medium">Dilution</th>
                      <th className="pb-2 font-medium">Ownership</th>
                    </tr>
                  </thead>
                  <tbody>
                    {mutation.data.rounds.map((r) => (
                      <tr key={r.round_label} className="border-b">
                        <td className="py-2 font-medium">{r.round_label}</td>
                        <td className="py-2">{formatCurrency(r.raise_amount)}</td>
                        <td className="py-2">{formatCurrency(r.post_money)}</td>
                        <td className="py-2">{r.dilution_pct.toFixed(1)}%</td>
                        <td className="py-2 font-semibold">
                          {r.founder_ownership_pct.toFixed(1)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Exit scenarios */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm">
                <DollarSign className="h-4 w-4" />
                Exit Scenarios
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3 sm:grid-cols-4">
                {mutation.data.exit_scenarios.map((exit) => (
                  <div
                    key={exit.exit_multiple}
                    className="rounded-lg border p-3 text-center"
                  >
                    <div className="text-xs text-muted-foreground">
                      {exit.exit_multiple}x Exit
                    </div>
                    <div className="text-lg font-bold">
                      {formatCurrency(exit.founder_proceeds)}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {formatCurrency(exit.exit_valuation)} valuation
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
