"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useStreaming } from "@/lib/hooks/useStreaming";
import { useUIStore } from "@/lib/stores/uiStore";
import { BookOpen, CheckCircle2 } from "lucide-react";

export function FundraisingPlaybook() {
  const activeWorkspaceId = useUIStore((s) => s.activeWorkspaceId);
  const streaming = useStreaming();
  const [targetRaise, setTargetRaise] = useState("");
  const [stage, setStage] = useState("seed");
  const [playbookResult, setPlaybookResult] = useState("");

  const handleGenerate = () => {
    if (!activeWorkspaceId) return;

    streaming.startStream(
      {
        workspace_id: activeWorkspaceId,
        content: `Create a real-time fundraising playbook for a ${stage} stage startup targeting a $${targetRaise || "2M"} raise. Include: (1) Pre-fundraise preparation checklist, (2) Timeline with milestones, (3) Investor targeting strategy, (4) Materials needed, (5) Meeting preparation tips, (6) Term sheet negotiation guide.`,
        override_agent: "venture-architect",
      },
      (_done, content) => {
        setPlaybookResult(content);
      }
    );
  };

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label>Target Raise ($)</Label>
          <Input
            value={targetRaise}
            onChange={(e) => setTargetRaise(e.target.value)}
            placeholder="2000000"
          />
        </div>
        <div className="space-y-2">
          <Label>Stage</Label>
          <Input
            value={stage}
            onChange={(e) => setStage(e.target.value)}
            placeholder="seed, series_a, etc."
          />
        </div>
      </div>

      <Button onClick={handleGenerate} disabled={streaming.isStreaming || !activeWorkspaceId}>
        <BookOpen className="mr-1 h-4 w-4" />
        {streaming.isStreaming ? "Generating..." : "Generate Playbook"}
      </Button>

      {(streaming.isStreaming || playbookResult) && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              <CheckCircle2 className="h-4 w-4" />
              Fundraising Playbook
              {streaming.isStreaming && (
                <span className="inline-flex h-2 w-2 animate-pulse rounded-full bg-green-500" />
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="whitespace-pre-wrap text-sm">
              {streaming.isStreaming ? streaming.streamingContent : playbookResult}
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
