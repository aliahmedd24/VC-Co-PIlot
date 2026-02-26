"use client";

import { useState, useCallback, useRef } from "react";
import { sendMessageStreaming } from "@/lib/api/chat";
import type {
  SendMessageRequest,
  SSERoutingEvent,
  SSEDoneEvent,
  SSEToolCallEvent,
  SSEToolResultEvent,
} from "@/lib/types";

interface StreamingState {
  isStreaming: boolean;
  streamingContent: string;
  routingEvent: SSERoutingEvent | null;
  doneEvent: SSEDoneEvent | null;
  activeTools: string[];
  toolResults: string[];
  error: string | null;
}

export function useStreaming() {
  const [state, setState] = useState<StreamingState>({
    isStreaming: false,
    streamingContent: "",
    routingEvent: null,
    doneEvent: null,
    activeTools: [],
    toolResults: [],
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
        activeTools: [],
        toolResults: [],
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
        onToolCall: (data: SSEToolCallEvent) => {
          setState((prev) => ({
            ...prev,
            activeTools: [...prev.activeTools, data.tool],
          }));
        },
        onToolResult: (data: SSEToolResultEvent) => {
          setState((prev) => ({
            ...prev,
            activeTools: prev.activeTools.filter((t) => t !== data.tool),
            toolResults: [...prev.toolResults, data.tool],
          }));
        },
        onDone: (data: SSEDoneEvent) => {
          setState((prev) => ({
            ...prev,
            isStreaming: false,
            activeTools: [],
            doneEvent: data,
          }));
          onComplete?.(data, contentRef.current);
        },
        onError: (error: Error) => {
          setState((prev) => ({
            ...prev,
            isStreaming: false,
            activeTools: [],
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
      activeTools: [],
      toolResults: [],
      error: null,
    });
  }, []);

  return {
    ...state,
    startStream,
    reset,
  };
}
