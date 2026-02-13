"use client";

import { useState, useMemo, useCallback, useEffect, useRef } from "react";
import { useUIStore } from "@/lib/stores/uiStore";
import { useChatSessions, useChatSession } from "@/lib/hooks/useChat";
import { useStreaming } from "@/lib/hooks/useStreaming";
import { ChatSidebar } from "@/components/chat/ChatSidebar";
import { MessageInput } from "@/components/chat/MessageInput";
import { StreamingMessage } from "@/components/chat/StreamingMessage";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MessageSquare } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { resolveAgentIcon } from "@/components/chat/agentIcons";
import { getAllAgents } from "@/lib/utils/agentMeta";
import { MessageRole } from "@/lib/types";
import type { ChatMessage, RoutingPlan } from "@/lib/types";
import { useQueryClient } from "@tanstack/react-query";

export default function ChatPage() {
  const activeWorkspaceId = useUIStore((s) => s.activeWorkspaceId);
  const activeSessionId = useUIStore((s) => s.activeSessionId);
  const setActiveSession = useUIStore((s) => s.setActiveSession);
  const queryClient = useQueryClient();

  const { data: sessionsData, isLoading: sessionsLoading } =
    useChatSessions(activeWorkspaceId);
  const { data: sessionData } = useChatSession(activeSessionId);
  const streaming = useStreaming();
  const bottomRef = useRef<HTMLDivElement>(null);

  const [optimisticMessages, setOptimisticMessages] = useState<ChatMessage[]>([]);
  const [lastRoutingPlan, setLastRoutingPlan] = useState<RoutingPlan | null>(null);

  const displayMessages = useMemo(() => {
    const serverMessages = sessionData?.messages ?? [];
    return [...serverMessages, ...optimisticMessages];
  }, [sessionData?.messages, optimisticMessages]);

  // Auto-scroll on new messages or streaming content
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [displayMessages.length, streaming.streamingContent]);

  const handleSend = useCallback(
    (content: string, agentOverride?: string | null) => {
      if (!activeWorkspaceId) return;

      const optimisticMsg: ChatMessage = {
        id: `temp-${Date.now()}`,
        role: MessageRole.USER,
        content,
        agent_id: null,
        citations: null,
        artifact_id: null,
        created_at: new Date().toISOString(),
      };
      setOptimisticMessages((prev) => [...prev, optimisticMsg]);

      streaming.startStream(
        {
          workspace_id: activeWorkspaceId,
          content,
          session_id: activeSessionId,
          override_agent: agentOverride ?? null,
        },
        () => {
          setOptimisticMessages([]);
          if (streaming.routingEvent) {
            setLastRoutingPlan(streaming.routingEvent as RoutingPlan);
          }
          queryClient.invalidateQueries({ queryKey: ["chatSessions"] });
          queryClient.invalidateQueries({ queryKey: ["chatSession"] });
        }
      );
    },
    [activeWorkspaceId, activeSessionId, streaming, queryClient]
  );

  const handleNewChat = useCallback(() => {
    setActiveSession(null);
    setOptimisticMessages([]);
    setLastRoutingPlan(null);
    streaming.reset();
  }, [setActiveSession, streaming]);

  const handleSelectSession = useCallback(
    (sessionId: string) => {
      setActiveSession(sessionId);
      setOptimisticMessages([]);
      setLastRoutingPlan(null);
      streaming.reset();
    },
    [setActiveSession, streaming]
  );

  const isLoading = streaming.isStreaming;
  const showEmptyState =
    displayMessages.length === 0 && !isLoading && !streaming.streamingContent;

  return (
    <div className="flex h-[calc(100vh-3.5rem)] -m-4 md:-m-6">
      <ChatSidebar
        sessions={sessionsData?.sessions ?? []}
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onNewChat={handleNewChat}
        isLoading={sessionsLoading}
      />

      <div className="flex flex-1 flex-col">
        {showEmptyState ? (
          <div className="flex flex-1 flex-col items-center justify-center text-muted-foreground">
            <MessageSquare className="mb-4 h-12 w-12" />
            <h3 className="mb-2 text-lg font-medium text-foreground">
              Start a conversation
            </h3>
            <p className="mb-6 max-w-sm text-center text-sm">
              Ask anything about your venture. Type{" "}
              <kbd className="rounded border bg-muted px-1 py-0.5 text-xs">@</kbd>{" "}
              to direct your question to a specific agent.
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
        ) : (
          <ScrollArea className="flex-1">
            <div className="space-y-4 p-4">
              {displayMessages.map((msg, i) => {
                let routingPlan: RoutingPlan | null = null;
                if (msg.role === MessageRole.ASSISTANT) {
                  const isLastAssistant = !displayMessages
                    .slice(i + 1)
                    .some((m) => m.role === MessageRole.ASSISTANT);
                  if (isLastAssistant && !streaming.isStreaming)
                    routingPlan = lastRoutingPlan;
                }
                return (
                  <MessageBubble
                    key={msg.id}
                    message={msg}
                    routingPlan={routingPlan}
                  />
                );
              })}

              {streaming.isStreaming && (
                <StreamingMessage
                  content={streaming.streamingContent}
                  routingEvent={streaming.routingEvent}
                />
              )}

              <div ref={bottomRef} />
            </div>
          </ScrollArea>
        )}

        <MessageInput
          onSend={handleSend}
          disabled={isLoading || !activeWorkspaceId}
        />
      </div>
    </div>
  );
}
