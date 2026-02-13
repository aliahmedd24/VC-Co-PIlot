import { apiClient } from "./client";
import type { Workspace, Venture, VentureUpdateRequest } from "@/lib/types";

export async function createWorkspace(name: string): Promise<Workspace> {
  const { data } = await apiClient.post<Workspace>("/workspaces", { name });
  return data;
}

export async function getWorkspaces(): Promise<Workspace[]> {
  const { data } = await apiClient.get<Workspace[]>("/workspaces");
  return data;
}

export async function getWorkspace(id: string): Promise<Workspace> {
  const { data } = await apiClient.get<Workspace>(`/workspaces/${id}`);
  return data;
}

export async function updateVenture(
  workspaceId: string,
  updates: VentureUpdateRequest
): Promise<Venture> {
  const { data } = await apiClient.patch<Venture>(
    `/workspaces/${workspaceId}/venture`,
    updates
  );
  return data;
}
