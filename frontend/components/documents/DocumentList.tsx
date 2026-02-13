"use client";

import { FileText } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { formatFileSize, formatRelativeTime } from "@/lib/utils/formatters";
import { DocumentStatus } from "@/lib/types";
import type { Document } from "@/lib/types";

interface DocumentListProps {
  documents: Document[];
  isLoading: boolean;
}

function formatDocType(type: string): string {
  return type
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

function statusBadge(status: DocumentStatus) {
  switch (status) {
    case DocumentStatus.PENDING:
      return <Badge variant="secondary">Pending</Badge>;
    case DocumentStatus.PROCESSING:
      return <Badge variant="default">Processing</Badge>;
    case DocumentStatus.INDEXED:
      return (
        <Badge className="bg-green-600 hover:bg-green-700 text-white">
          Indexed
        </Badge>
      );
    case DocumentStatus.FAILED:
      return <Badge variant="destructive">Failed</Badge>;
    default:
      return <Badge variant="secondary">{status}</Badge>;
  }
}

export function DocumentList({ documents, isLoading }: DocumentListProps) {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="h-14 animate-pulse rounded-lg border bg-muted"
          />
        ))}
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
        <FileText className="mb-3 h-10 w-10" />
        <p className="text-sm font-medium">No documents yet</p>
        <p className="text-xs">Upload your first document above.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b bg-muted/50">
            <th className="px-4 py-2 text-left font-medium">Name</th>
            <th className="hidden px-4 py-2 text-left font-medium sm:table-cell">
              Type
            </th>
            <th className="hidden px-4 py-2 text-left font-medium md:table-cell">
              Size
            </th>
            <th className="px-4 py-2 text-left font-medium">Status</th>
            <th className="hidden px-4 py-2 text-left font-medium sm:table-cell">
              Uploaded
            </th>
          </tr>
        </thead>
        <tbody>
          {documents.map((doc) => (
            <tr key={doc.id} className="border-b last:border-0">
              <td className="px-4 py-3">
                <span className="font-medium truncate block max-w-[200px]" title={doc.name}>
                  {doc.name}
                </span>
              </td>
              <td className="hidden px-4 py-3 text-muted-foreground sm:table-cell">
                {formatDocType(doc.type)}
              </td>
              <td className="hidden px-4 py-3 text-muted-foreground md:table-cell">
                {formatFileSize(doc.size)}
              </td>
              <td className="px-4 py-3">{statusBadge(doc.status)}</td>
              <td className="hidden px-4 py-3 text-muted-foreground sm:table-cell">
                {formatRelativeTime(doc.created_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
