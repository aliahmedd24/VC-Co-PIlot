import { apiClient } from "./client";
import type {
  BrainSearchRequest,
  BrainSearchResponse,
  VentureProfile,
  EntityCreateRequest,
  EntityUpdateRequest,
  EntityResult,
} from "@/lib/types";

export async function search(
  req: BrainSearchRequest
): Promise<BrainSearchResponse> {
  const { data } = await apiClient.post<BrainSearchResponse>(
    "/brain/search",
    req
  );
  return data;
}

export async function getProfile(
  workspaceId: string
): Promise<VentureProfile> {
  const { data } = await apiClient.get<VentureProfile>(
    `/brain/profile/${workspaceId}`
  );
  return data;
}

export async function createEntity(
  req: EntityCreateRequest
): Promise<EntityResult> {
  const { data } = await apiClient.post<EntityResult>(
    "/brain/entities",
    req
  );
  return data;
}

export async function updateEntity(
  id: string,
  req: EntityUpdateRequest
): Promise<EntityResult> {
  const { data } = await apiClient.patch<EntityResult>(
    `/brain/entities/${id}`,
    req
  );
  return data;
}

export async function deleteEntity(id: string): Promise<void> {
  await apiClient.delete(`/brain/entities/${id}`);
}
