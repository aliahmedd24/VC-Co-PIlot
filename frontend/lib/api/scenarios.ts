import { apiClient } from "./client";
import type { ScenarioRequest, ScenarioModelResult } from "@/lib/types";

export async function getScenarios(
  req: ScenarioRequest
): Promise<ScenarioModelResult> {
  const { data } = await apiClient.post<ScenarioModelResult>(
    "/scenarios",
    req
  );
  return data;
}
