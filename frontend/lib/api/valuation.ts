import { apiClient } from "./client";
import type { ValuationRequest, ValuationResult } from "@/lib/types";

export async function getValuation(
  req: ValuationRequest
): Promise<ValuationResult> {
  const { data } = await apiClient.post<ValuationResult>(
    "/valuation",
    req
  );
  return data;
}
