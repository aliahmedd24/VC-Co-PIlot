"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { getAgentMeta } from "@/lib/utils/agentMeta";
import {
  getConfidenceColor,
  getConfidenceLabel,
} from "@/lib/utils/confidenceColor";
import type { RoutingPlan } from "@/lib/types";

interface RoutingDetailsProps {
  routingPlan: RoutingPlan;
}

function formatModelProfile(profile: string): string {
  return profile
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

export function RoutingDetails({ routingPlan }: RoutingDetailsProps) {
  const [expanded, setExpanded] = useState(false);
  const agent = getAgentMeta(routingPlan.selected_agent);

  return (
    <div className="mt-2">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
      >
        {expanded ? (
          <ChevronUp className="h-3 w-3" />
        ) : (
          <ChevronDown className="h-3 w-3" />
        )}
        Routing details
      </button>

      {expanded && (
        <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 rounded-md border bg-muted/50 p-3 text-xs">
          <span className="text-muted-foreground">Agent</span>
          <span className="font-medium">{agent.name}</span>

          <span className="text-muted-foreground">Model</span>
          <span>{formatModelProfile(routingPlan.model_profile)}</span>

          <span className="text-muted-foreground">Confidence</span>
          <span>
            <Badge
              variant="secondary"
              className={`${getConfidenceColor(routingPlan.confidence)} text-white text-[10px] px-1.5 py-0`}
            >
              {getConfidenceLabel(routingPlan.confidence)} (
              {(routingPlan.confidence * 100).toFixed(0)}%)
            </Badge>
          </span>

          <span className="text-muted-foreground">Latency</span>
          <span>{routingPlan.latency_ms}ms</span>

          {routingPlan.tools.length > 0 && (
            <>
              <span className="text-muted-foreground">Tools</span>
              <span>{routingPlan.tools.join(", ")}</span>
            </>
          )}

          <span className="col-span-2 mt-1 text-muted-foreground">
            {routingPlan.reasoning}
          </span>
        </div>
      )}
    </div>
  );
}
