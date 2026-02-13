"use client";

import { ArtifactType } from "@/lib/types";
import { LeanCanvasRenderer } from "./LeanCanvasRenderer";
import { DeckOutlineRenderer } from "./DeckOutlineRenderer";
import { FinancialModelRenderer } from "./FinancialModelRenderer";
import { KPIDashboardRenderer } from "./KPIDashboardRenderer";

interface ArtifactRendererProps {
  type: ArtifactType;
  content: Record<string, unknown>;
}

function GenericRenderer({ content }: { content: Record<string, unknown> }) {
  return (
    <div className="space-y-3">
      {Object.entries(content).map(([key, value]) => (
        <div key={key}>
          <h4 className="text-xs font-semibold uppercase text-muted-foreground">
            {key.replace(/_/g, " ")}
          </h4>
          <div className="mt-1 text-sm whitespace-pre-wrap">
            {typeof value === "string"
              ? value
              : typeof value === "object" && value !== null
                ? JSON.stringify(value, null, 2)
                : String(value ?? "")}
          </div>
        </div>
      ))}
      {Object.keys(content).length === 0 && (
        <p className="text-sm text-muted-foreground italic">
          No content yet.
        </p>
      )}
    </div>
  );
}

export function ArtifactRenderer({ type, content }: ArtifactRendererProps) {
  switch (type) {
    case ArtifactType.LEAN_CANVAS:
      return <LeanCanvasRenderer content={content} />;
    case ArtifactType.DECK_OUTLINE:
      return <DeckOutlineRenderer content={content} />;
    case ArtifactType.FINANCIAL_MODEL:
      return <FinancialModelRenderer content={content} />;
    case ArtifactType.KPI_DASHBOARD:
      return <KPIDashboardRenderer content={content} />;
    default:
      return <GenericRenderer content={content} />;
  }
}
