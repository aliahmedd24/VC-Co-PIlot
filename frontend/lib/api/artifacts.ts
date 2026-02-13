import { apiClient } from "./client";
import type {
  Artifact,
  ArtifactCreateRequest,
  ArtifactUpdateRequest,
  ArtifactListResponse,
  ArtifactVersion,
  ArtifactVersionListResponse,
  SendMessageResponse,
  ExportTaskResponse,
} from "@/lib/types";

export async function createArtifact(
  req: ArtifactCreateRequest
): Promise<Artifact> {
  const { data } = await apiClient.post<Artifact>("/artifacts", req);
  return data;
}

export async function getArtifacts(
  workspaceId: string
): Promise<ArtifactListResponse> {
  const { data } = await apiClient.get<ArtifactListResponse>("/artifacts", {
    params: { workspace_id: workspaceId },
  });
  return data;
}

export async function getArtifact(id: string): Promise<Artifact> {
  const { data } = await apiClient.get<Artifact>(`/artifacts/${id}`);
  return data;
}

export async function updateArtifact(
  id: string,
  req: ArtifactUpdateRequest
): Promise<Artifact> {
  const { data } = await apiClient.patch<Artifact>(`/artifacts/${id}`, req);
  return data;
}

export async function getVersions(
  id: string
): Promise<ArtifactVersionListResponse> {
  const { data } = await apiClient.get<ArtifactVersionListResponse>(
    `/artifacts/${id}/versions`
  );
  return data;
}

export async function getVersion(
  id: string,
  version: number
): Promise<ArtifactVersion> {
  const { data } = await apiClient.get<ArtifactVersion>(
    `/artifacts/${id}/versions/${version}`
  );
  return data;
}

export async function artifactChat(
  id: string,
  content: string
): Promise<SendMessageResponse> {
  const { data } = await apiClient.post<SendMessageResponse>(
    `/artifacts/${id}/chat`,
    { content }
  );
  return data;
}

export async function exportArtifact(
  id: string,
  format: "markdown" | "pdf"
): Promise<string | ExportTaskResponse> {
  const { data } = await apiClient.post(`/artifacts/${id}/export`, { format });
  return data as string | ExportTaskResponse;
}
