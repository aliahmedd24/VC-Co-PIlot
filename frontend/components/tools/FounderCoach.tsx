"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { useStreaming } from "@/lib/hooks/useStreaming";
import { useUIStore } from "@/lib/stores/uiStore";
import { UserCircle, MessageSquare } from "lucide-react";

export function FounderCoach() {
  const activeWorkspaceId = useUIStore((s) => s.activeWorkspaceId);
  const streaming = useStreaming();
  const [bio, setBio] = useState("");
  const [coachingResult, setCoachingResult] = useState("");

  const handleCoach = () => {
    if (!activeWorkspaceId || !bio.trim()) return;

    streaming.startStream(
      {
        workspace_id: activeWorkspaceId,
        content: `As a founder persona coach, analyze this founder bio and provide feedback on how to position themselves for investor meetings. Focus on strengths, gaps, and specific improvements:\n\n${bio}`,
        override_agent: "venture-architect",
      },
      (_done, content) => {
        setCoachingResult(content);
      }
    );
  };

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Label>Founder Bio / Background</Label>
        <textarea
          className="flex min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          value={bio}
          onChange={(e) => setBio(e.target.value)}
          placeholder="Describe the founder's background, experience, skills, and relevant achievements..."
        />
      </div>

      <Button onClick={handleCoach} disabled={streaming.isStreaming || !activeWorkspaceId || !bio.trim()}>
        <UserCircle className="mr-1 h-4 w-4" />
        {streaming.isStreaming ? "Coaching..." : "Get Coaching Feedback"}
      </Button>

      {(streaming.isStreaming || coachingResult) && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              <MessageSquare className="h-4 w-4" />
              Coaching Feedback
              {streaming.isStreaming && (
                <span className="inline-flex h-2 w-2 animate-pulse rounded-full bg-green-500" />
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="whitespace-pre-wrap text-sm">
              {streaming.isStreaming ? streaming.streamingContent : coachingResult}
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
