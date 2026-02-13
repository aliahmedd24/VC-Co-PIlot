"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { EntityCard } from "./EntityCard";
import type { EntityResult, EntityUpdateRequest } from "@/lib/types";

interface EntityTypeSectionProps {
  type: string;
  entities: EntityResult[];
  onUpdate: (id: string, updates: EntityUpdateRequest) => void;
  onDelete: (id: string) => void;
}

function formatTypeName(type: string): string {
  return type
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

export function EntityTypeSection({
  type,
  entities,
  onUpdate,
  onDelete,
}: EntityTypeSectionProps) {
  const [expanded, setExpanded] = useState(true);

  return (
    <div data-testid="entity-type-section">
      <button
        className="flex w-full items-center gap-2 py-2 text-left"
        onClick={() => setExpanded(!expanded)}
      >
        {expanded ? (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronRight className="h-4 w-4 text-muted-foreground" />
        )}
        <h3 className="text-sm font-semibold">{formatTypeName(type)}</h3>
        <Badge variant="secondary" className="text-[10px]">
          {entities.length}
        </Badge>
      </button>
      {expanded && (
        <div className="ml-6 space-y-2 pb-2">
          {entities.map((entity) => (
            <EntityCard
              key={entity.id}
              entity={entity}
              onUpdate={onUpdate}
              onDelete={onDelete}
            />
          ))}
        </div>
      )}
    </div>
  );
}
