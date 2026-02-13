import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { uploadDocument, getDocuments } from "@/lib/api/documents";
import { toast } from "@/lib/hooks/useToast";

export function useDocuments(workspaceId: string | null) {
  return useQuery({
    queryKey: ["documents", workspaceId],
    queryFn: () => getDocuments(workspaceId!),
    enabled: !!workspaceId,
  });
}

export function useUploadDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      workspaceId,
      file,
      onProgress,
    }: {
      workspaceId: string;
      file: File;
      onProgress?: (percent: number) => void;
    }) => uploadDocument(workspaceId, file, onProgress),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      toast({
        title: "Document uploaded",
        description: "Your document is being processed.",
      });
    },
    onError: () => {
      toast({
        variant: "destructive",
        title: "Upload failed",
        description: "Failed to upload document.",
      });
    },
  });
}
