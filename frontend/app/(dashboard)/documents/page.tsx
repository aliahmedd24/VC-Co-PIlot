"use client";

import { useUIStore } from "@/lib/stores/uiStore";
import { useDocuments } from "@/lib/hooks/useDocuments";
import { UploadDropzone } from "@/components/documents/UploadDropzone";
import { DocumentList } from "@/components/documents/DocumentList";

export default function DocumentsPage() {
  const activeWorkspaceId = useUIStore((s) => s.activeWorkspaceId);
  const { data: docsData, isLoading } = useDocuments(activeWorkspaceId);

  if (!activeWorkspaceId) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center text-muted-foreground">
        <p className="text-sm">Select a workspace to manage documents.</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Documents</h1>
        <p className="text-sm text-muted-foreground">
          Upload and manage your venture documents.
        </p>
      </div>

      <UploadDropzone workspaceId={activeWorkspaceId} />

      <DocumentList
        documents={docsData?.documents ?? []}
        isLoading={isLoading}
      />
    </div>
  );
}
