import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createWorkspace,
  getWorkspaces,
  getWorkspace,
  updateVenture,
} from "@/lib/api/workspaces";
import type { VentureUpdateRequest } from "@/lib/types";
import { toast } from "@/lib/hooks/useToast";

export function useWorkspaces() {
  return useQuery({
    queryKey: ["workspaces"],
    queryFn: getWorkspaces,
  });
}

export function useWorkspace(id: string | null) {
  return useQuery({
    queryKey: ["workspace", id],
    queryFn: () => getWorkspace(id!),
    enabled: !!id,
  });
}

export function useCreateWorkspace() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (name: string) => createWorkspace(name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspaces"] });
    },
    onError: () => {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to create workspace.",
      });
    },
  });
}

export function useUpdateVenture() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      workspaceId,
      updates,
    }: {
      workspaceId: string;
      updates: VentureUpdateRequest;
    }) => updateVenture(workspaceId, updates),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["workspace", variables.workspaceId],
      });
      queryClient.invalidateQueries({ queryKey: ["workspaces"] });
    },
    onError: () => {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to update venture.",
      });
    },
  });
}
