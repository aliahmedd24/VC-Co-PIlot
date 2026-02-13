import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { search, getProfile, updateEntity, deleteEntity } from "@/lib/api/brain";
import type { BrainSearchRequest, EntityUpdateRequest } from "@/lib/types";
import { toast } from "@/lib/hooks/useToast";

export function useVentureProfile(workspaceId: string | null) {
  return useQuery({
    queryKey: ["ventureProfile", workspaceId],
    queryFn: () => getProfile(workspaceId!),
    enabled: !!workspaceId,
  });
}

export function useBrainSearch() {
  return useMutation({
    mutationFn: (req: BrainSearchRequest) => search(req),
    onError: () => {
      toast({
        variant: "destructive",
        title: "Search failed",
        description: "Brain search encountered an error.",
      });
    },
  });
}

export function useUpdateEntity() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      updates,
    }: {
      id: string;
      updates: EntityUpdateRequest;
    }) => updateEntity(id, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ventureProfile"] });
    },
    onError: () => {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to update entity.",
      });
    },
  });
}

export function useDeleteEntity() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteEntity(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ventureProfile"] });
    },
    onError: () => {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to delete entity.",
      });
    },
  });
}
