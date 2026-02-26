import { apiClient } from "./client";
import type {
  SendMessageRequest,
  SendMessageResponse,
  ChatSessionListResponse,
  ChatSession,
} from "@/lib/types";

export async function sendMessage(
  req: SendMessageRequest
): Promise<SendMessageResponse> {
  const { data } = await apiClient.post<SendMessageResponse>(
    "/chat/send",
    req
  );
  return data;
}

export async function getSessions(
  workspaceId: string
): Promise<ChatSessionListResponse> {
  const { data } = await apiClient.get<ChatSessionListResponse>(
    "/chat/sessions",
    {
      params: { workspace_id: workspaceId },
    }
  );
  return data;
}

export async function getSession(sessionId: string): Promise<ChatSession> {
  const { data } = await apiClient.get<ChatSession>(
    `/chat/sessions/${sessionId}`
  );
  return data;
}

export interface StreamCallbacks {
  onRouting: (data: import("@/lib/types").SSERoutingEvent) => void;
  onToken: (token: string) => void;
  onDone: (data: import("@/lib/types").SSEDoneEvent) => void;
  onError: (error: Error) => void;
  onToolCall?: (data: import("@/lib/types").SSEToolCallEvent) => void;
  onToolResult?: (data: import("@/lib/types").SSEToolResultEvent) => void;
}

export async function sendMessageStreaming(
  req: SendMessageRequest,
  callbacks: StreamCallbacks
): Promise<void> {
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("access_token")
      : null;

  const response = await fetch(`${API_URL}/api/v1/chat/send`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(req),
  });

  if (!response.ok) {
    callbacks.onError(new Error(`HTTP ${response.status}`));
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    callbacks.onError(new Error("No response body"));
    return;
  }

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    let currentEvent = "";
    for (const line of lines) {
      if (line.startsWith("event: ")) {
        currentEvent = line.slice(7).trim();
      } else if (line.startsWith("data: ") && currentEvent) {
        const data = line.slice(6);
        try {
          if (currentEvent === "routing") {
            callbacks.onRouting(JSON.parse(data));
          } else if (currentEvent === "token") {
            callbacks.onToken(JSON.parse(data));
          } else if (currentEvent === "tool_call") {
            callbacks.onToolCall?.(JSON.parse(data));
          } else if (currentEvent === "tool_result") {
            callbacks.onToolResult?.(JSON.parse(data));
          } else if (currentEvent === "done") {
            callbacks.onDone(JSON.parse(data));
          }
        } catch {
          // skip malformed JSON
        }
        currentEvent = "";
      }
    }
  }
}
