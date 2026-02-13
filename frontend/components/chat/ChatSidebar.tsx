"use client";

import { MessageSquare, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { formatRelativeTime } from "@/lib/utils/formatters";
import type { ChatSession } from "@/lib/types";

interface ChatSidebarProps {
  sessions: ChatSession[];
  activeSessionId: string | null;
  onSelectSession: (sessionId: string) => void;
  onNewChat: () => void;
  isLoading: boolean;
}

export function ChatSidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewChat,
  isLoading,
}: ChatSidebarProps) {
  return (
    <div className="hidden w-72 flex-shrink-0 flex-col border-r bg-muted/30 md:flex">
      <div className="p-3">
        <Button onClick={onNewChat} variant="outline" className="w-full gap-2">
          <Plus className="h-4 w-4" />
          New Chat
        </Button>
      </div>

      <Separator />

      <ScrollArea className="flex-1">
        {isLoading ? (
          <div className="space-y-2 p-3">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-12 animate-pulse rounded-md bg-muted"
              />
            ))}
          </div>
        ) : sessions.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
            <MessageSquare className="mb-2 h-8 w-8" />
            <p className="text-xs">No conversations yet</p>
          </div>
        ) : (
          <div className="space-y-1 p-2">
            {sessions.map((session) => (
              <button
                key={session.id}
                type="button"
                onClick={() => onSelectSession(session.id)}
                className={`w-full rounded-md px-3 py-2 text-left transition-colors ${
                  session.id === activeSessionId
                    ? "bg-accent"
                    : "hover:bg-accent/50"
                }`}
              >
                <p className="truncate text-sm font-medium">
                  {session.title ?? "Untitled"}
                </p>
                <p className="text-[10px] text-muted-foreground">
                  {formatRelativeTime(session.updated_at)}
                </p>
              </button>
            ))}
          </div>
        )}
      </ScrollArea>
    </div>
  );
}
