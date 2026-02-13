"use client";

import { useState } from "react";
import {
  ArrowLeft,
  Download,
  Send,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { VersionSelector } from "./VersionSelector";
import { ArtifactRenderer } from "./ArtifactRenderer";
import { VersionDiff } from "./VersionDiff";
import {
  useArtifact,
  useArtifactVersions,
  useUpdateArtifact,
  useExportArtifact,
} from "@/lib/hooks/useArtifacts";
import { ArtifactStatus } from "@/lib/types";
import type { ArtifactVersion } from "@/lib/types";
import { getAgentMeta } from "@/lib/utils/agentMeta";
import { formatRelativeTime } from "@/lib/utils/formatters";
import { toast } from "@/lib/hooks/useToast";
import { artifactChat } from "@/lib/api/artifacts";

interface ArtifactDetailProps {
  artifactId: string;
  onBack: () => void;
}

function statusBadge(status: ArtifactStatus) {
  switch (status) {
    case ArtifactStatus.DRAFT:
      return <Badge variant="secondary">Draft</Badge>;
    case ArtifactStatus.IN_PROGRESS:
      return <Badge variant="default">In Progress</Badge>;
    case ArtifactStatus.READY:
      return (
        <Badge className="bg-green-600 hover:bg-green-700 text-white">
          Ready
        </Badge>
      );
    case ArtifactStatus.ARCHIVED:
      return <Badge variant="outline">Archived</Badge>;
    default:
      return <Badge variant="secondary">{status}</Badge>;
  }
}

export function ArtifactDetail({ artifactId, onBack }: ArtifactDetailProps) {
  const { data: artifact, isLoading: artifactLoading } =
    useArtifact(artifactId);
  const { data: versionsData } = useArtifactVersions(artifactId);
  const updateArtifact = useUpdateArtifact();
  const exportMutation = useExportArtifact();

  const [selectedVersion, setSelectedVersion] = useState<number | null>(null);
  const [compareVersion, setCompareVersion] = useState<number | null>(null);
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState<
    { role: "user" | "assistant"; content: string }[]
  >([]);
  const [chatLoading, setChatLoading] = useState(false);

  const versions = versionsData?.versions ?? [];
  const displayVersion = selectedVersion ?? artifact?.current_version ?? 1;

  const currentVersionData = versions.find(
    (v) => v.version === displayVersion
  );
  const compareVersionData = compareVersion
    ? versions.find((v) => v.version === compareVersion)
    : null;

  const displayContent =
    currentVersionData?.content ?? artifact?.content ?? {};

  async function handleStatusChange(newStatus: ArtifactStatus) {
    if (!artifact) return;
    updateArtifact.mutate({
      id: artifact.id,
      updates: {
        status: newStatus,
        expected_version: artifact.current_version,
      },
    });
  }

  async function handleExport(format: "markdown" | "pdf") {
    if (!artifact) return;
    exportMutation.mutate(
      { id: artifact.id, format },
      {
        onSuccess: (data) => {
          if (typeof data === "string") {
            const blob = new Blob([data], { type: "text/markdown" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `${artifact.title}.md`;
            a.click();
            URL.revokeObjectURL(url);
          } else {
            toast({
              title: "Export started",
              description:
                "PDF export queued. Check back shortly for download.",
            });
          }
        },
      }
    );
  }

  async function handleChatSend() {
    if (!chatInput.trim() || !artifact) return;
    const content = chatInput.trim();
    setChatInput("");
    setChatMessages((prev) => [...prev, { role: "user", content }]);
    setChatLoading(true);

    try {
      const response = await artifactChat(artifact.id, content);
      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", content: response.assistant_message.content },
      ]);
    } catch {
      toast({
        variant: "destructive",
        title: "Chat error",
        description: "Failed to get a response.",
      });
    } finally {
      setChatLoading(false);
    }
  }

  if (artifactLoading || !artifact) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const agent = getAgentMeta(artifact.owner_agent);

  return (
    <div className="flex h-full flex-col">
      {/* Top bar */}
      <div className="flex flex-wrap items-center gap-3 border-b pb-3">
        <Button variant="ghost" size="icon" onClick={onBack}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <h2 className="text-lg font-semibold truncate max-w-[300px]">
          {artifact.title}
        </h2>
        <div
          className="cursor-pointer"
          onClick={() => {
            const statuses = Object.values(ArtifactStatus);
            const currentIdx = statuses.indexOf(artifact.status);
            const nextStatus =
              statuses[(currentIdx + 1) % statuses.length];
            handleStatusChange(nextStatus);
          }}
          data-testid="status-badge"
        >
          {statusBadge(artifact.status)}
        </div>
        <span className="text-xs text-muted-foreground">{agent.name}</span>

        <div className="ml-auto flex items-center gap-2">
          {versions.length > 0 && (
            <VersionSelector
              versions={versions}
              currentVersion={displayVersion}
              onVersionChange={setSelectedVersion}
            />
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleExport("markdown")}
            disabled={exportMutation.isPending}
            data-testid="export-md-btn"
          >
            <Download className="mr-1 h-3 w-3" />
            MD
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleExport("pdf")}
            disabled={exportMutation.isPending}
          >
            <Download className="mr-1 h-3 w-3" />
            PDF
          </Button>
        </div>
      </div>

      {/* Version comparison selector */}
      {versions.length > 1 && (
        <div className="flex items-center gap-2 border-b py-2">
          <span className="text-xs text-muted-foreground">Compare with:</span>
          <Select
            value={compareVersion ? String(compareVersion) : "none"}
            onValueChange={(v) =>
              setCompareVersion(v === "none" ? null : Number(v))
            }
          >
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="None" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">None</SelectItem>
              {versions
                .filter((v) => v.version !== displayVersion)
                .map((v) => (
                  <SelectItem key={v.version} value={String(v.version)}>
                    v{v.version} · {formatRelativeTime(v.created_at)}
                  </SelectItem>
                ))}
            </SelectContent>
          </Select>
        </div>
      )}

      {/* Main content area */}
      <div className="flex flex-1 gap-0 overflow-hidden">
        {/* Left: rendered artifact */}
        <div className="flex-1 overflow-auto p-4">
          {compareVersionData && currentVersionData ? (
            <VersionDiff
              versionA={currentVersionData}
              versionB={compareVersionData}
            />
          ) : (
            <ArtifactRenderer
              type={artifact.type}
              content={displayContent}
            />
          )}
        </div>

        {/* Right: artifact chat */}
        <div className="hidden w-80 flex-col border-l lg:flex">
          <div className="border-b px-3 py-2">
            <h3 className="text-sm font-semibold">Refine with AI</h3>
            <p className="text-xs text-muted-foreground">
              Chat to improve this artifact
            </p>
          </div>
          <ScrollArea className="flex-1 p-3">
            <div className="space-y-3">
              {chatMessages.map((msg, i) => (
                <div
                  key={i}
                  className={`rounded-lg px-3 py-2 text-sm ${
                    msg.role === "user"
                      ? "ml-4 bg-primary text-primary-foreground"
                      : "mr-4 bg-muted"
                  }`}
                >
                  {msg.content}
                </div>
              ))}
              {chatLoading && (
                <div className="mr-4 rounded-lg bg-muted px-3 py-2 text-sm">
                  <span className="animate-pulse">Thinking...</span>
                </div>
              )}
            </div>
          </ScrollArea>
          <div className="border-t p-3">
            <div className="flex gap-2">
              <Textarea
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Suggest changes..."
                className="min-h-[60px] resize-none text-sm"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleChatSend();
                  }
                }}
              />
              <Button
                size="icon"
                onClick={handleChatSend}
                disabled={!chatInput.trim() || chatLoading}
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
