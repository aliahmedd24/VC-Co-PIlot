"use client";

import { FileBox } from "lucide-react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { getAgentMeta } from "@/lib/utils/agentMeta";
import { resolveAgentIcon } from "@/components/chat/agentIcons";
import { RoutingDetails } from "@/components/chat/RoutingDetails";
import { formatRelativeTime } from "@/lib/utils/formatters";
import { MessageRole } from "@/lib/types";
import type { ChatMessage, RoutingPlan } from "@/lib/types";

interface MessageBubbleProps {
  message: ChatMessage;
  routingPlan?: RoutingPlan | null;
  isLoading?: boolean;
}

export function MessageBubble({
  message,
  routingPlan,
  isLoading,
}: MessageBubbleProps) {
  // Loading / thinking state
  if (isLoading) {
    return (
      <div className="flex justify-start">
        <div className="max-w-[80%] rounded-lg bg-muted px-4 py-3">
          <div className="flex items-center gap-2">
            <div className="flex gap-1">
              <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/60 [animation-delay:-0.3s]" />
              <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/60 [animation-delay:-0.15s]" />
              <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/60" />
            </div>
            <span className="text-xs text-muted-foreground">Thinking...</span>
          </div>
        </div>
      </div>
    );
  }

  const isUser = message.role === MessageRole.USER;

  // User message
  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%]">
          <div className="rounded-lg bg-primary px-4 py-3 text-primary-foreground">
            <p className="whitespace-pre-wrap text-sm">{message.content}</p>
          </div>
          <p className="mt-1 text-right text-[10px] text-muted-foreground">
            {formatRelativeTime(message.created_at)}
          </p>
        </div>
      </div>
    );
  }

  // Assistant message
  const agent = getAgentMeta(message.agent_id);
  const AgentIcon = resolveAgentIcon(agent.icon);

  return (
    <div className="flex justify-start">
      <div className="max-w-[80%]">
        {/* Agent badge */}
        <div className="mb-1 flex items-center gap-1.5">
          <AgentIcon className={`h-3.5 w-3.5 ${agent.color}`} />
          <span className={`text-xs font-medium ${agent.color}`}>
            {agent.name}
          </span>
        </div>

        {/* Message content */}
        <div className="rounded-lg bg-muted px-4 py-3">
          <p className="whitespace-pre-wrap text-sm">{message.content}</p>

          {/* Citations */}
          {message.citations && message.citations.length > 0 && (
            <div className="mt-3 space-y-1 border-t pt-2">
              <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">
                Sources
              </p>
              {message.citations.map((citation, i) => (
                <div
                  key={i}
                  className="rounded border bg-background px-2 py-1 text-xs text-muted-foreground"
                >
                  <span className="font-medium">
                    {(citation.content as string)?.slice(0, 80) ?? "Document"}
                    {((citation.content as string)?.length ?? 0) > 80
                      ? "..."
                      : ""}
                  </span>
                  {citation.similarity != null && (
                    <span className="ml-2 text-[10px]">
                      ({((citation.similarity as number) * 100).toFixed(0)}%
                      match)
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Artifact link */}
          {message.artifact_id && (
            <Link
              href={`/artifacts?id=${message.artifact_id}`}
              className="mt-2 flex items-center gap-2 rounded border bg-background px-3 py-2 text-xs hover:bg-accent transition-colors"
            >
              <FileBox className="h-4 w-4 text-muted-foreground" />
              <span className="font-medium">View Artifact</span>
            </Link>
          )}

          {/* Routing details */}
          {routingPlan && <RoutingDetails routingPlan={routingPlan} />}
        </div>

        <p className="mt-1 text-[10px] text-muted-foreground">
          {formatRelativeTime(message.created_at)}
        </p>
      </div>
    </div>
  );
}
