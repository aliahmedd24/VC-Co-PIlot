import { apiClient } from "./client";
import type {
  BenchmarkRequest,
  BenchmarkResult,
  SuccessStoryRequest,
  SuccessStoryResult,
} from "@/lib/types";

export async function getBenchmarks(
  req: BenchmarkRequest
): Promise<BenchmarkResult> {
  const { data } = await apiClient.post<BenchmarkResult>(
    "/benchmarks",
    req
  );
  return data;
}

export async function getSuccessStories(
  req: SuccessStoryRequest
): Promise<SuccessStoryResult> {
  const { data } = await apiClient.post<SuccessStoryResult>(
    "/benchmarks/success-stories",
    req
  );
  return data;
}
