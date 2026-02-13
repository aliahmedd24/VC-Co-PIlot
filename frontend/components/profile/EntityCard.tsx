"use client";

import {
  CheckCircle,
  Pin,
  Trash2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { getConfidenceColor, getConfidenceLabel } from "@/lib/utils/confidenceColor";
import { KGEntityStatus } from "@/lib/types";
import type { EntityResult, EntityUpdateRequest } from "@/lib/types";

interface EntityCardProps {
  entity: EntityResult;
  onUpdate: (id: string, updates: EntityUpdateRequest) => void;
  onDelete: (id: string) => void;
}

function statusBadge(status: KGEntityStatus) {
  switch (status) {
    case KGEntityStatus.CONFIRMED:
      return (
        <Badge className="bg-green-600 hover:bg-green-700 text-white text-[10px]">
          Confirmed
        </Badge>
      );
    case KGEntityStatus.NEEDS_REVIEW:
      return (
        <Badge variant="default" className="text-[10px]">
          Needs Review
        </Badge>
      );
    case KGEntityStatus.SUGGESTED:
      return (
        <Badge variant="secondary" className="text-[10px]">
          Suggested
        </Badge>
      );
    case KGEntityStatus.PINNED:
      return (
        <Badge variant="outline" className="text-[10px]">
          Pinned
        </Badge>
      );
    default:
      return <Badge variant="secondary" className="text-[10px]">{status}</Badge>;
  }
}

export function EntityCard({ entity, onUpdate, onDelete }: EntityCardProps) {
  const dataEntries = Object.entries(entity.data).filter(
    ([key]) => key !== "id" && key !== "type"
  );

  return (
    <Card data-testid="entity-card">
      <CardContent className="p-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              {statusBadge(entity.status)}
              <div className="flex items-center gap-1">
                <div
                  className={`h-2 w-2 rounded-full ${getConfidenceColor(entity.confidence)}`}
                />
                <span className="text-[10px] text-muted-foreground">
                  {getConfidenceLabel(entity.confidence)} ({Math.round(entity.confidence * 100)}%)
                </span>
              </div>
              <span className="text-[10px] text-muted-foreground">
                {entity.evidence_count} evidence
              </span>
            </div>
            <dl className="mt-2 space-y-1">
              {dataEntries.slice(0, 4).map(([key, value]) => (
                <div key={key}>
                  <dt className="text-[10px] font-medium text-muted-foreground uppercase">
                    {key.replace(/_/g, " ")}
                  </dt>
                  <dd className="text-xs truncate" title={String(value)}>
                    {typeof value === "object" && value !== null
                      ? JSON.stringify(value)
                      : String(value ?? "")}
                  </dd>
                </div>
              ))}
              {dataEntries.length > 4 && (
                <p className="text-[10px] text-muted-foreground">
                  +{dataEntries.length - 4} more fields
                </p>
              )}
            </dl>
          </div>
          <div className="flex flex-col gap-1">
            {entity.status !== KGEntityStatus.CONFIRMED && (
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                title="Confirm"
                data-testid="confirm-entity-btn"
                onClick={() =>
                  onUpdate(entity.id, {
                    status: KGEntityStatus.CONFIRMED,
                  })
                }
              >
                <CheckCircle className="h-3 w-3 text-green-600" />
              </Button>
            )}
            {entity.status !== KGEntityStatus.PINNED && (
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                title="Pin"
                onClick={() =>
                  onUpdate(entity.id, {
                    status: KGEntityStatus.PINNED,
                  })
                }
              >
                <Pin className="h-3 w-3" />
              </Button>
            )}
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              title="Delete"
              onClick={() => onDelete(entity.id)}
            >
              <Trash2 className="h-3 w-3 text-red-500" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
