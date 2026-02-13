import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { sendMessage, getSessions, getSession } from "@/lib/api/chat";
import type { SendMessageRequest } from "@/lib/types";
import { toast } from "@/lib/hooks/useToast";

export function useChatSessions(workspaceId: string | null) {
  return useQuery({
    queryKey: ["chatSessions", workspaceId],
    queryFn: () => getSessions(workspaceId!),
    enabled: !!workspaceId,
  });
}

export function useChatSession(sessionId: string | null) {
  return useQuery({
    queryKey: ["chatSession", sessionId],
    queryFn: () => getSession(sessionId!),
    enabled: !!sessionId,
  });
}

export function useSendMessage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (req: SendMessageRequest) => sendMessage(req),
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: ["chatSession", data.session_id],
      });
      queryClient.invalidateQueries({ queryKey: ["chatSessions"] });
    },
    onError: () => {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to send message. Please try again.",
      });
    },
  });
}
