"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useStreaming } from "@/lib/hooks/useStreaming";
import { useUIStore } from "@/lib/stores/uiStore";
import { Globe, MapPin } from "lucide-react";

export function ExpansionAdvisor() {
  const activeWorkspaceId = useUIStore((s) => s.activeWorkspaceId);
  const streaming = useStreaming();
  const [targetMarket, setTargetMarket] = useState("");
  const [currentMarket, setCurrentMarket] = useState("");
  const [analysisResult, setAnalysisResult] = useState("");

  const handleAnalyze = () => {
    if (!activeWorkspaceId) return;

    streaming.startStream(
      {
        workspace_id: activeWorkspaceId,
        content: `As a cross-border expansion advisor, analyze expanding from ${currentMarket || "domestic market"} to ${targetMarket || "international markets"}. Include regulatory considerations, market sizing, competitive landscape, go-to-market strategy, and cultural factors.`,
        override_agent: "market-oracle",
      },
      (_done, content) => {
        setAnalysisResult(content);
      }
    );
  };

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label>Current Market</Label>
          <Input
            value={currentMarket}
            onChange={(e) => setCurrentMarket(e.target.value)}
            placeholder="e.g. United States"
          />
        </div>
        <div className="space-y-2">
          <Label>Target Market</Label>
          <Input
            value={targetMarket}
            onChange={(e) => setTargetMarket(e.target.value)}
            placeholder="e.g. Europe, Southeast Asia"
          />
        </div>
      </div>

      <Button onClick={handleAnalyze} disabled={streaming.isStreaming || !activeWorkspaceId}>
        <Globe className="mr-1 h-4 w-4" />
        {streaming.isStreaming ? "Analyzing..." : "Analyze Expansion"}
      </Button>

      {(streaming.isStreaming || analysisResult) && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              <MapPin className="h-4 w-4" />
              Expansion Analysis
              {streaming.isStreaming && (
                <span className="inline-flex h-2 w-2 animate-pulse rounded-full bg-green-500" />
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="whitespace-pre-wrap text-sm">
              {streaming.isStreaming ? streaming.streamingContent : analysisResult}
              {streaming.isStreaming && (
                <span className="inline-block h-4 w-0.5 animate-pulse bg-foreground/60 ml-0.5" />
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
