"use client";

import { useEffect, useRef } from "react";
import { MessageSquare } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { resolveAgentIcon } from "@/components/chat/agentIcons";
import { getAllAgents } from "@/lib/utils/agentMeta";
import { MessageRole } from "@/lib/types";
import type { ChatMessage, RoutingPlan } from "@/lib/types";

interface MessageThreadProps {
  messages: ChatMessage[];
  lastRoutingPlan?: RoutingPlan | null;
  isLoading: boolean;
}

export function MessageThread({
  messages,
  lastRoutingPlan,
  isLoading,
}: MessageThreadProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, isLoading]);

  // Empty / welcome state
  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center text-muted-foreground">
        <MessageSquare className="mb-4 h-12 w-12" />
        <h3 className="mb-2 text-lg font-medium text-foreground">
          Start a conversation
        </h3>
        <p className="mb-6 max-w-sm text-center text-sm">
          Ask anything about your venture. Type <kbd className="rounded border bg-muted px-1 py-0.5 text-xs">@</kbd> to direct your question to a specific agent.
        </p>
        <div className="flex flex-wrap justify-center gap-2">
          {getAllAgents().map((agent) => {
            const Icon = resolveAgentIcon(agent.icon);
            return (
              <Badge key={agent.id} variant="secondary" className="gap-1">
                <Icon className={`h-3 w-3 ${agent.color}`} />
                <span className="text-xs">{agent.name}</span>
              </Badge>
            );
          })}
        </div>
      </div>
    );
  }

  // Find the last assistant message index to attach routing plan
  let lastAssistantIndex = -1;
  for (let i = messages.length - 1; i >= 0; i--) {
    if (messages[i].role === MessageRole.ASSISTANT) {
      lastAssistantIndex = i;
      break;
    }
  }

  return (
    <ScrollArea className="flex-1">
      <div className="space-y-4 p-4">
        {messages.map((msg, i) => (
          <MessageBubble
            key={msg.id}
            message={msg}
            routingPlan={i === lastAssistantIndex ? lastRoutingPlan : null}
          />
        ))}

        {/* Loading / thinking indicator */}
        {isLoading && <MessageBubble message={{} as ChatMessage} isLoading />}

        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}
