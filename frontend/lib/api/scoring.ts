import { apiClient } from "./client";
import type { InvestorReadinessScore } from "@/lib/types";

export async function getReadinessScore(
  workspaceId: string
): Promise<InvestorReadinessScore> {
  const { data } = await apiClient.post<InvestorReadinessScore>(
    "/scoring/readiness",
    { workspace_id: workspaceId }
  );
  return data;
}
