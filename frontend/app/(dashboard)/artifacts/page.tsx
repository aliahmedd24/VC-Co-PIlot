"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArtifactGrid } from "@/components/artifacts/ArtifactGrid";
import { useArtifacts } from "@/lib/hooks/useArtifacts";
import { useUIStore } from "@/lib/stores/uiStore";

export default function ArtifactsPage() {
  const router = useRouter();
  const activeWorkspaceId = useUIStore((s) => s.activeWorkspaceId);
  const { data, isLoading } = useArtifacts(activeWorkspaceId);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  function handleSelect(id: string) {
    setSelectedId(id);
    router.push(`/artifacts/${id}`);
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold">Artifacts</h1>
        <p className="text-sm text-muted-foreground">
          View and manage generated artifacts from your AI conversations.
        </p>
      </div>
      <ArtifactGrid
        artifacts={data?.artifacts ?? []}
        isLoading={isLoading}
        onSelect={handleSelect}
      />
    </div>
  );
}
