"use client";

import { useMutation } from "@tanstack/react-query";
import { getValuation } from "@/lib/api/valuation";
import { getReadinessScore } from "@/lib/api/scoring";
import { getScenarios } from "@/lib/api/scenarios";
import { getBenchmarks, getSuccessStories } from "@/lib/api/benchmarks";
import type {
  ValuationRequest,
  ScenarioRequest,
  BenchmarkRequest,
  SuccessStoryRequest,
} from "@/lib/types";
import { toast } from "@/lib/hooks/useToast";

export function useValuation() {
  return useMutation({
    mutationFn: (req: ValuationRequest) => getValuation(req),
    onError: () => {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to compute valuation.",
      });
    },
  });
}

export function useReadinessScore() {
  return useMutation({
    mutationFn: (workspaceId: string) => getReadinessScore(workspaceId),
    onError: () => {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to compute readiness score.",
      });
    },
  });
}

export function useScenarios() {
  return useMutation({
    mutationFn: (req: ScenarioRequest) => getScenarios(req),
    onError: () => {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to compute scenarios.",
      });
    },
  });
}

export function useBenchmarks() {
  return useMutation({
    mutationFn: (req: BenchmarkRequest) => getBenchmarks(req),
    onError: () => {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to fetch benchmarks.",
      });
    },
  });
}

export function useSuccessStories() {
  return useMutation({
    mutationFn: (req: SuccessStoryRequest) => getSuccessStories(req),
    onError: () => {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to fetch success stories.",
      });
    },
  });
}
