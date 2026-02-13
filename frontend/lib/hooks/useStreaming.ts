"use client";

import { useState, useCallback, useRef } from "react";
import { sendMessageStreaming } from "@/lib/api/chat";
import type {
  SendMessageRequest,
  SSERoutingEvent,
  SSEDoneEvent,
} from "@/lib/types";

interface StreamingState {
  isStreaming: boolean;
  streamingContent: string;
  routingEvent: SSERoutingEvent | null;
  doneEvent: SSEDoneEvent | null;
  error: string | null;
}

export function useStreaming() {
  const [state, setState] = useState<StreamingState>({
    isStreaming: false,
    streamingContent: "",
    routingEvent: null,
    doneEvent: null,
    error: null,
  });

  const contentRef = useRef("");

  const startStream = useCallback(
    async (
      req: SendMessageRequest,
      onComplete?: (doneEvent: SSEDoneEvent, content: string) => void
    ) => {
      contentRef.current = "";
      setState({
        isStreaming: true,
        streamingContent: "",
        routingEvent: null,
        doneEvent: null,
        error: null,
      });

      await sendMessageStreaming(req, {
        onRouting: (data: SSERoutingEvent) => {
          setState((prev) => ({ ...prev, routingEvent: data }));
        },
        onToken: (token: string) => {
          contentRef.current += token;
          setState((prev) => ({
            ...prev,
            streamingContent: contentRef.current,
          }));
        },
        onDone: (data: SSEDoneEvent) => {
          setState((prev) => ({
            ...prev,
            isStreaming: false,
            doneEvent: data,
          }));
          onComplete?.(data, contentRef.current);
        },
        onError: (error: Error) => {
          setState((prev) => ({
            ...prev,
            isStreaming: false,
            error: error.message,
          }));
        },
      });
    },
    []
  );

  const reset = useCallback(() => {
    contentRef.current = "";
    setState({
      isStreaming: false,
      streamingContent: "",
      routingEvent: null,
      doneEvent: null,
      error: null,
    });
  }, []);

  return {
    ...state,
    startStream,
    reset,
  };
}
