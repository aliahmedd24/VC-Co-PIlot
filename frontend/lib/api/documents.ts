import { apiClient } from "./client";
import type { Document, DocumentListResponse } from "@/lib/types";

export async function uploadDocument(
  workspaceId: string,
  file: File,
  onProgress?: (percent: number) => void
): Promise<Document> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("workspace_id", workspaceId);

  const { data } = await apiClient.post<Document>(
    "/documents/upload",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percent = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(percent);
        }
      },
    }
  );
  return data;
}

export async function getDocuments(
  workspaceId: string
): Promise<DocumentListResponse> {
  const { data } = await apiClient.get<DocumentListResponse>("/documents", {
    params: { workspace_id: workspaceId },
  });
  return data;
}
