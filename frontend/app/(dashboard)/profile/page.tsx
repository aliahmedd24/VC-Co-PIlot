"use client";

import { Loader2, FileText, Brain } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import { VentureHeader } from "@/components/profile/VentureHeader";
import { EntityTypeSection } from "@/components/profile/EntityTypeSection";
import { MetricsOverview } from "@/components/profile/MetricsOverview";
import { useVentureProfile, useUpdateEntity, useDeleteEntity } from "@/lib/hooks/useBrain";
import { useUpdateVenture } from "@/lib/hooks/useWorkspace";
import { useUIStore } from "@/lib/stores/uiStore";
import { KGEntityType } from "@/lib/types";

export default function ProfilePage() {
  const activeWorkspaceId = useUIStore((s) => s.activeWorkspaceId);
  const { data: profile, isLoading } = useVentureProfile(activeWorkspaceId);
  const updateVenture = useUpdateVenture();
  const updateEntity = useUpdateEntity();
  const deleteEntity = useDeleteEntity();

  if (!activeWorkspaceId) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
        <Brain className="mb-3 h-12 w-12" />
        <p className="text-sm">Select a workspace to view the venture profile.</p>
      </div>
    );
  }

  if (isLoading || !profile) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const entityTypes = Object.entries(profile.entities_by_type);
  const metricEntities =
    profile.entities_by_type[KGEntityType.METRIC] ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Venture Profile</h1>
        <p className="text-sm text-muted-foreground">
          Overview of your venture, knowledge graph entities, and key metrics.
        </p>
      </div>

      {/* Venture Info */}
      <VentureHeader
        venture={profile.venture}
        workspaceId={activeWorkspaceId}
        onUpdate={(updates) =>
          updateVenture.mutate({
            workspaceId: activeWorkspaceId,
            updates,
          })
        }
        isUpdating={updateVenture.isPending}
      />

      {/* Summary stats */}
      <div className="flex gap-6 text-sm text-muted-foreground">
        <div className="flex items-center gap-1">
          <FileText className="h-4 w-4" />
          {profile.total_documents} documents
        </div>
        <div className="flex items-center gap-1">
          <Brain className="h-4 w-4" />
          {profile.total_entities} entities
        </div>
      </div>

      {/* Metrics Overview */}
      {metricEntities.length > 0 && (
        <>
          <Separator />
          <div>
            <h2 className="mb-3 text-lg font-semibold">Key Metrics</h2>
            <MetricsOverview metrics={metricEntities} />
          </div>
        </>
      )}

      {/* Knowledge Graph Entities */}
      <Separator />
      <div>
        <h2 className="mb-3 text-lg font-semibold">Knowledge Graph</h2>
        {entityTypes.length === 0 ? (
          <div className="py-8 text-center text-sm text-muted-foreground">
            No entities extracted yet. Upload documents to populate your
            knowledge graph.
          </div>
        ) : (
          <div className="space-y-1" data-testid="entity-sections">
            {entityTypes.map(([type, entities]) => (
              <EntityTypeSection
                key={type}
                type={type}
                entities={entities}
                onUpdate={(id, updates) =>
                  updateEntity.mutate({ id, updates })
                }
                onDelete={(id) => deleteEntity.mutate(id)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
