"use client";

import { useState, useRef, useCallback } from "react";
import { Send, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { AgentSelector } from "@/components/chat/AgentSelector";
import { getAgentMeta } from "@/lib/utils/agentMeta";

interface MessageInputProps {
  onSend: (content: string, agentOverride?: string | null) => void;
  disabled: boolean;
}

export function MessageInput({ onSend, disabled }: MessageInputProps) {
  const [content, setContent] = useState("");
  const [agentOverride, setAgentOverride] = useState<string | null>(null);
  const [showAgentSelector, setShowAgentSelector] = useState(false);
  const [mentionFilter, setMentionFilter] = useState("");
  const [mentionStart, setMentionStart] = useState<number | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = useCallback(() => {
    const trimmed = content.trim();
    if (!trimmed) return;
    onSend(trimmed, agentOverride);
    setContent("");
    setAgentOverride(null);
    setShowAgentSelector(false);
    setMentionFilter("");
    setMentionStart(null);
  }, [content, agentOverride, onSend]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey && !showAgentSelector) {
        e.preventDefault();
        if (!disabled) {
          handleSend();
        }
      }
    },
    [handleSend, disabled, showAgentSelector]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const value = e.target.value;
      setContent(value);

      // Detect @mention
      const cursorPos = e.target.selectionStart ?? value.length;
      const textBeforeCursor = value.slice(0, cursorPos);
      const lastAtIndex = textBeforeCursor.lastIndexOf("@");

      if (lastAtIndex >= 0) {
        const charBefore = lastAtIndex > 0 ? value[lastAtIndex - 1] : " ";
        if (charBefore === " " || charBefore === "\n" || lastAtIndex === 0) {
          const filter = textBeforeCursor.slice(lastAtIndex + 1);
          if (!filter.includes(" ")) {
            setShowAgentSelector(true);
            setMentionFilter(filter);
            setMentionStart(lastAtIndex);
            return;
          }
        }
      }

      setShowAgentSelector(false);
      setMentionFilter("");
      setMentionStart(null);
    },
    []
  );

  const handleAgentSelect = useCallback(
    (agentId: string) => {
      setAgentOverride(agentId);
      setShowAgentSelector(false);
      setMentionFilter("");

      // Remove the @filter text from content
      if (mentionStart != null) {
        const cursorPos = textareaRef.current?.selectionStart ?? content.length;
        const before = content.slice(0, mentionStart);
        const after = content.slice(cursorPos);
        setContent(before + after);
      }

      setMentionStart(null);
      textareaRef.current?.focus();
    },
    [mentionStart, content]
  );

  const handleClearOverride = useCallback(() => {
    setAgentOverride(null);
  }, []);

  return (
    <div className="border-t bg-background p-4">
      {/* Agent override badge */}
      {agentOverride && (
        <div className="mb-2 flex items-center gap-1">
          <Badge variant="secondary" className="gap-1">
            <span className="text-xs">@{getAgentMeta(agentOverride).name}</span>
            <button
              type="button"
              onClick={handleClearOverride}
              className="ml-0.5 rounded-full hover:bg-muted-foreground/20"
            >
              <X className="h-3 w-3" />
            </button>
          </Badge>
        </div>
      )}

      <div className="relative flex items-end gap-2">
        {/* Agent selector dropdown */}
        <AgentSelector
          open={showAgentSelector}
          onSelect={handleAgentSelect}
          onClose={() => {
            setShowAgentSelector(false);
            setMentionFilter("");
            setMentionStart(null);
          }}
          filter={mentionFilter}
        />

        <Textarea
          ref={textareaRef}
          value={content}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder="Type a message... (@ to mention an agent)"
          disabled={disabled}
          rows={1}
          className="min-h-[40px] max-h-[160px] resize-none flex-1"
        />

        <Button
          size="icon"
          onClick={handleSend}
          disabled={disabled || !content.trim()}
          aria-label="Send message"
        >
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
