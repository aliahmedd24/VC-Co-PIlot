"use client";

import { getAgentMeta } from "@/lib/utils/agentMeta";
import { resolveAgentIcon } from "@/components/chat/agentIcons";
import type { SSERoutingEvent } from "@/lib/types";

interface StreamingMessageProps {
  content: string;
  routingEvent: SSERoutingEvent | null;
  activeTools?: string[];
  toolResults?: string[];
}

/** Convert snake_case tool name to a readable label, e.g. "run_valuation" → "Running Valuation" */
function toolDisplayName(name: string): string {
  // Short CVC words that need consonant doubling before -ing
  const doubleConsonant = new Set(["run", "get", "set", "put", "cut", "hit", "map", "log"]);
  const words = name.split("_");
  if (words.length === 0) return name;
  const first = words[0];
  const rest = words.slice(1).map((w) => w.charAt(0).toUpperCase() + w.slice(1));
  let gerund: string;
  if (first.endsWith("e")) {
    gerund = first.slice(0, -1) + "ing";
  } else if (doubleConsonant.has(first)) {
    gerund = first + first.charAt(first.length - 1) + "ing";
  } else {
    gerund = first + "ing";
  }
  return [gerund.charAt(0).toUpperCase() + gerund.slice(1), ...rest].join(" ");
}

export function StreamingMessage({
  content,
  routingEvent,
  activeTools = [],
  toolResults = [],
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

        {/* Tool activity indicators */}
        {(activeTools.length > 0 || toolResults.length > 0) && (
          <div className="mb-2 flex flex-wrap gap-1.5" data-testid="tool-activity">
            {activeTools.map((tool) => (
              <span
                key={`active-${tool}`}
                className="inline-flex items-center gap-1 rounded-full bg-amber-500/15 px-2.5 py-0.5 text-xs font-medium text-amber-700 dark:text-amber-400"
                data-testid={`tool-active-${tool}`}
              >
                <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-amber-500" />
                {toolDisplayName(tool)}
              </span>
            ))}
            {toolResults.map((tool) => (
              <span
                key={`done-${tool}`}
                className="inline-flex items-center gap-1 rounded-full bg-emerald-500/15 px-2.5 py-0.5 text-xs font-medium text-emerald-700 dark:text-emerald-400"
                data-testid={`tool-done-${tool}`}
              >
                <svg
                  className="h-3 w-3"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2.5}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M5 13l4 4L19 7"
                  />
                </svg>
                {toolDisplayName(tool)}
              </span>
            ))}
          </div>
        )}

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
              <span className="text-xs text-muted-foreground">
                {activeTools.length > 0
                  ? `Using ${toolDisplayName(activeTools[0])}...`
                  : "Generating..."}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
