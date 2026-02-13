"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useStreaming } from "@/lib/hooks/useStreaming";
import { useUIStore } from "@/lib/stores/uiStore";
import { Presentation, Sparkles } from "lucide-react";

export function PitchGenerator() {
  const activeWorkspaceId = useUIStore((s) => s.activeWorkspaceId);
  const streaming = useStreaming();
  const [audience, setAudience] = useState("VC investors");
  const [tone, setTone] = useState("professional");
  const [generatedPitch, setGeneratedPitch] = useState("");

  const handleGenerate = () => {
    if (!activeWorkspaceId) return;

    streaming.startStream(
      {
        workspace_id: activeWorkspaceId,
        content: `Generate a compelling pitch narrative for ${audience}. Tone: ${tone}. Include the problem, solution, market size, traction, team, and ask.`,
        override_agent: "storyteller",
      },
      (_done, content) => {
        setGeneratedPitch(content);
      }
    );
  };

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label>Target Audience</Label>
          <Input
            value={audience}
            onChange={(e) => setAudience(e.target.value)}
            placeholder="VC investors, angels, etc."
          />
        </div>
        <div className="space-y-2">
          <Label>Tone</Label>
          <Input
            value={tone}
            onChange={(e) => setTone(e.target.value)}
            placeholder="professional, bold, etc."
          />
        </div>
      </div>

      <Button onClick={handleGenerate} disabled={streaming.isStreaming || !activeWorkspaceId}>
        <Sparkles className="mr-1 h-4 w-4" />
        {streaming.isStreaming ? "Generating..." : "Generate Pitch"}
      </Button>

      {(streaming.isStreaming || generatedPitch) && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Presentation className="h-4 w-4" />
              Generated Pitch
              {streaming.isStreaming && (
                <span className="inline-flex h-2 w-2 animate-pulse rounded-full bg-green-500" />
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="whitespace-pre-wrap text-sm">
              {streaming.isStreaming ? streaming.streamingContent : generatedPitch}
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
