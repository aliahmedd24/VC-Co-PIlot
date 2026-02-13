import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createArtifact,
  getArtifacts,
  getArtifact,
  updateArtifact,
  getVersions,
  exportArtifact,
} from "@/lib/api/artifacts";
import type { ArtifactCreateRequest, ArtifactUpdateRequest } from "@/lib/types";
import { toast } from "@/lib/hooks/useToast";

export function useArtifacts(workspaceId: string | null) {
  return useQuery({
    queryKey: ["artifacts", workspaceId],
    queryFn: () => getArtifacts(workspaceId!),
    enabled: !!workspaceId,
  });
}

export function useArtifact(id: string | null) {
  return useQuery({
    queryKey: ["artifact", id],
    queryFn: () => getArtifact(id!),
    enabled: !!id,
  });
}

export function useCreateArtifact() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (req: ArtifactCreateRequest) => createArtifact(req),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["artifacts"] });
    },
    onError: () => {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to create artifact.",
      });
    },
  });
}

export function useUpdateArtifact() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      updates,
    }: {
      id: string;
      updates: ArtifactUpdateRequest;
    }) => updateArtifact(id, updates),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["artifact", variables.id],
      });
      queryClient.invalidateQueries({ queryKey: ["artifacts"] });
    },
    onError: () => {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to update artifact.",
      });
    },
  });
}

export function useArtifactVersions(id: string | null) {
  return useQuery({
    queryKey: ["artifactVersions", id],
    queryFn: () => getVersions(id!),
    enabled: !!id,
  });
}

export function useExportArtifact() {
  return useMutation({
    mutationFn: ({
      id,
      format,
    }: {
      id: string;
      format: "markdown" | "pdf";
    }) => exportArtifact(id, format),
    onError: () => {
      toast({
        variant: "destructive",
        title: "Export failed",
        description: "Failed to export artifact.",
      });
    },
  });
}
