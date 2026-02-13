"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { RadarChart } from "@/components/charts/RadarChart";
import { useReadinessScore } from "@/lib/hooks/useTools";
import { useUIStore } from "@/lib/stores/uiStore";
import { Shield, AlertCircle, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils/cn";

function gradeColor(grade: string): string {
  if (grade === "A") return "text-green-600";
  if (grade === "B") return "text-blue-600";
  if (grade === "C") return "text-yellow-600";
  if (grade === "D") return "text-orange-600";
  return "text-red-600";
}

export function ReadinessScoreCard() {
  const activeWorkspaceId = useUIStore((s) => s.activeWorkspaceId);
  const mutation = useReadinessScore();

  const handleScore = () => {
    if (activeWorkspaceId) {
      mutation.mutate(activeWorkspaceId);
    }
  };

  const radarData = mutation.data?.dimensions.map((d) => ({
    subject: d.name,
    value: (d.score / d.max_score) * 100,
    fullMark: 100,
  }));

  return (
    <div className="space-y-6">
      <Button onClick={handleScore} disabled={mutation.isPending || !activeWorkspaceId}>
        {mutation.isPending ? "Analyzing..." : "Check Investor Readiness"}
      </Button>

      {mutation.data && (
        <div className="space-y-4">
          {/* Overall score */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm">
                <Shield className="h-4 w-4" />
                Investor Readiness Score
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-4">
                <div className={cn("text-5xl font-bold", gradeColor(mutation.data.grade))}>
                  {mutation.data.grade}
                </div>
                <div>
                  <div className="text-2xl font-semibold">
                    {mutation.data.overall_score.toFixed(0)}/100
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {mutation.data.summary}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Radar chart */}
          {radarData && <RadarChart data={radarData} />}

          {/* Dimension cards */}
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {mutation.data.dimensions.map((dim) => (
              <Card key={dim.name}>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">{dim.name}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex items-center gap-2">
                    <div className="h-2 flex-1 rounded-full bg-muted">
                      <div
                        className="h-full rounded-full bg-primary"
                        style={{
                          width: `${(dim.score / dim.max_score) * 100}%`,
                        }}
                      />
                    </div>
                    <span className="text-sm font-medium">
                      {dim.score}/{dim.max_score}
                    </span>
                  </div>
                  {dim.checks_passed.length > 0 && (
                    <ul className="space-y-0.5">
                      {dim.checks_passed.map((c, i) => (
                        <li key={i} className="flex items-center gap-1 text-xs text-green-600">
                          <CheckCircle2 className="h-3 w-3" />
                          {c}
                        </li>
                      ))}
                    </ul>
                  )}
                  {dim.checks_failed.length > 0 && (
                    <ul className="space-y-0.5">
                      {dim.checks_failed.map((c, i) => (
                        <li key={i} className="flex items-center gap-1 text-xs text-red-600">
                          <AlertCircle className="h-3 w-3" />
                          {c}
                        </li>
                      ))}
                    </ul>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Gaps & Recommendations */}
          {mutation.data.gaps.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Gaps & Recommendations</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <h4 className="text-xs font-medium text-muted-foreground uppercase mb-1">Gaps</h4>
                  <ul className="space-y-1">
                    {mutation.data.gaps.map((g, i) => (
                      <li key={i} className="flex items-center gap-1 text-sm">
                        <AlertCircle className="h-3 w-3 text-yellow-500" />
                        {g}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h4 className="text-xs font-medium text-muted-foreground uppercase mb-1">
                    Recommendations
                  </h4>
                  <ul className="space-y-1">
                    {mutation.data.recommendations.map((r, i) => (
                      <li key={i} className="text-sm text-muted-foreground">
                        {r}
                      </li>
                    ))}
                  </ul>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
