"use client";

import { getAgentMeta } from "@/lib/utils/agentMeta";
import { resolveAgentIcon } from "@/components/chat/agentIcons";
import type { SSERoutingEvent } from "@/lib/types";

interface StreamingMessageProps {
  content: string;
  routingEvent: SSERoutingEvent | null;
}

export function StreamingMessage({
  content,
  routingEvent,
}: StreamingMessageProps) {
  const agentId = routingEvent?.selected_agent ?? "venture-architect";
  const agent = getAgentMeta(agentId);
  const AgentIcon = resolveAgentIcon(agent.icon);

  return (
    <div className="flex justify-start">
      <div className="max-w-[80%]">
        <div className="mb-1 flex items-center gap-1.5">
          <AgentIcon className={`h-3.5 w-3.5 ${agent.color}`} />
          <span className={`text-xs font-medium ${agent.color}`}>
            {agent.name}
          </span>
          <span className="ml-1 inline-flex h-2 w-2 animate-pulse rounded-full bg-green-500" />
        </div>

        <div className="rounded-lg bg-muted px-4 py-3">
          {content ? (
            <p className="whitespace-pre-wrap text-sm">
              {content}
              <span className="inline-block h-4 w-0.5 animate-pulse bg-foreground/60 ml-0.5" />
            </p>
          ) : (
            <div className="flex items-center gap-2">
              <div className="flex gap-1">
                <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/60 [animation-delay:-0.3s]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/60 [animation-delay:-0.15s]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/60" />
              </div>
              <span className="text-xs text-muted-foreground">Generating...</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
