"use client";

import { useState } from "react";
import { FileBox, LayoutGrid, List } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatRelativeTime } from "@/lib/utils/formatters";
import { getAgentMeta } from "@/lib/utils/agentMeta";
import { ArtifactStatus, ArtifactType } from "@/lib/types";
import type { Artifact } from "@/lib/types";

interface ArtifactGridProps {
  artifacts: Artifact[];
  isLoading: boolean;
  onSelect: (id: string) => void;
}

function artifactTypeName(type: ArtifactType): string {
  return type
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
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

export function ArtifactGrid({
  artifacts,
  isLoading,
  onSelect,
}: ArtifactGridProps) {
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [filterType, setFilterType] = useState<string>("all");
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [sortBy, setSortBy] = useState<"updated" | "created">("updated");

  const filtered = artifacts
    .filter((a) => filterType === "all" || a.type === filterType)
    .filter((a) => filterStatus === "all" || a.status === filterStatus)
    .sort((a, b) => {
      const dateA =
        sortBy === "updated" ? a.updated_at : a.created_at;
      const dateB =
        sortBy === "updated" ? b.updated_at : b.created_at;
      return new Date(dateB).getTime() - new Date(dateA).getTime();
    });

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div
            key={i}
            className="h-36 animate-pulse rounded-lg border bg-muted"
          />
        ))}
      </div>
    );
  }

  if (artifacts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
        <FileBox className="mb-3 h-12 w-12" />
        <h3 className="text-base font-medium">No artifacts yet</h3>
        <p className="text-sm">
          Chat with an agent to generate your first artifact.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex flex-wrap items-center gap-3">
        <Select value={filterType} onValueChange={setFilterType}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            {Object.values(ArtifactType).map((t) => (
              <SelectItem key={t} value={t}>
                {artifactTypeName(t)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={filterStatus} onValueChange={setFilterStatus}>
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            {Object.values(ArtifactStatus).map((s) => (
              <SelectItem key={s} value={s}>
                {s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={sortBy}
          onValueChange={(v) => setSortBy(v as "updated" | "created")}
        >
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Sort" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="updated">Last Updated</SelectItem>
            <SelectItem value="created">Created</SelectItem>
          </SelectContent>
        </Select>

        <div className="ml-auto flex gap-1">
          <Button
            variant={viewMode === "grid" ? "default" : "outline"}
            size="icon"
            onClick={() => setViewMode("grid")}
          >
            <LayoutGrid className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === "list" ? "default" : "outline"}
            size="icon"
            onClick={() => setViewMode("list")}
          >
            <List className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Grid view */}
      {viewMode === "grid" ? (
        <div
          className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"
          data-testid="artifact-grid"
        >
          {filtered.map((artifact) => {
            const agent = getAgentMeta(artifact.owner_agent);
            return (
              <Card
                key={artifact.id}
                className="cursor-pointer transition-shadow hover:shadow-md"
                onClick={() => onSelect(artifact.id)}
                data-testid="artifact-card"
              >
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <CardTitle className="text-sm font-medium leading-tight line-clamp-2">
                      {artifact.title}
                    </CardTitle>
                    {statusBadge(artifact.status)}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>{artifactTypeName(artifact.type)}</span>
                    <span>v{artifact.current_version}</span>
                  </div>
                  <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
                    <span>{agent.name}</span>
                    <span>{formatRelativeTime(artifact.updated_at)}</span>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      ) : (
        /* List view */
        <div className="overflow-x-auto rounded-lg border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="px-4 py-2 text-left font-medium">Title</th>
                <th className="hidden px-4 py-2 text-left font-medium sm:table-cell">
                  Type
                </th>
                <th className="px-4 py-2 text-left font-medium">Status</th>
                <th className="hidden px-4 py-2 text-left font-medium md:table-cell">
                  Agent
                </th>
                <th className="hidden px-4 py-2 text-left font-medium sm:table-cell">
                  Updated
                </th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((artifact) => {
                const agent = getAgentMeta(artifact.owner_agent);
                return (
                  <tr
                    key={artifact.id}
                    className="cursor-pointer border-b last:border-0 hover:bg-muted/30"
                    onClick={() => onSelect(artifact.id)}
                  >
                    <td className="px-4 py-3">
                      <span
                        className="font-medium truncate block max-w-[250px]"
                        title={artifact.title}
                      >
                        {artifact.title}
                      </span>
                    </td>
                    <td className="hidden px-4 py-3 text-muted-foreground sm:table-cell">
                      {artifactTypeName(artifact.type)}
                    </td>
                    <td className="px-4 py-3">
                      {statusBadge(artifact.status)}
                    </td>
                    <td className="hidden px-4 py-3 text-muted-foreground md:table-cell">
                      {agent.name}
                    </td>
                    <td className="hidden px-4 py-3 text-muted-foreground sm:table-cell">
                      {formatRelativeTime(artifact.updated_at)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {filtered.length === 0 && artifacts.length > 0 && (
        <p className="py-8 text-center text-sm text-muted-foreground">
          No artifacts match the current filters.
        </p>
      )}
    </div>
  );
}
