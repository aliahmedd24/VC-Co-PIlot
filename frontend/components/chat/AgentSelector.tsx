"use client";

import { useEffect, useRef, useState } from "react";
import { Card } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { getAllAgents } from "@/lib/utils/agentMeta";
import { resolveAgentIcon } from "@/components/chat/agentIcons";

interface AgentSelectorProps {
  open: boolean;
  onSelect: (agentId: string) => void;
  onClose: () => void;
  filter: string;
}

export function AgentSelector({
  open,
  onSelect,
  onClose,
  filter,
}: AgentSelectorProps) {
  const [activeIndex, setActiveIndex] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  const agents = getAllAgents().filter((a) =>
    a.name.toLowerCase().includes(filter.toLowerCase())
  );

  useEffect(() => {
    setActiveIndex(0);
  }, [filter]);

  useEffect(() => {
    if (!open) return;

    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setActiveIndex((prev) => Math.min(prev + 1, agents.length - 1));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setActiveIndex((prev) => Math.max(prev - 1, 0));
      } else if (e.key === "Enter") {
        e.preventDefault();
        if (agents[activeIndex]) {
          onSelect(agents[activeIndex].id);
        }
      } else if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, activeIndex, agents, onSelect, onClose]);

  if (!open || agents.length === 0) return null;

  return (
    <Card
      ref={containerRef}
      className="absolute bottom-full left-0 mb-1 w-64 shadow-lg z-50"
    >
      <ScrollArea className="max-h-60">
        <div className="p-1">
          {agents.map((agent, i) => {
            const Icon = resolveAgentIcon(agent.icon);
            return (
              <button
                key={agent.id}
                type="button"
                className={`flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm transition-colors ${
                  i === activeIndex ? "bg-accent" : "hover:bg-accent/50"
                }`}
                onMouseEnter={() => setActiveIndex(i)}
                onClick={() => onSelect(agent.id)}
              >
                <Icon className={`h-4 w-4 ${agent.color}`} />
                <span>{agent.name}</span>
              </button>
            );
          })}
        </div>
      </ScrollArea>
    </Card>
  );
}
