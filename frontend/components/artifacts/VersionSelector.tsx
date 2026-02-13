"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { formatRelativeTime } from "@/lib/utils/formatters";
import type { ArtifactVersion } from "@/lib/types";

interface VersionSelectorProps {
  versions: ArtifactVersion[];
  currentVersion: number;
  onVersionChange: (version: number) => void;
}

export function VersionSelector({
  versions,
  currentVersion,
  onVersionChange,
}: VersionSelectorProps) {
  return (
    <Select
      value={String(currentVersion)}
      onValueChange={(val) => onVersionChange(Number(val))}
    >
      <SelectTrigger className="w-[160px]" data-testid="version-selector">
        <SelectValue placeholder="Select version" />
      </SelectTrigger>
      <SelectContent>
        {versions.map((v) => (
          <SelectItem key={v.version} value={String(v.version)}>
            v{v.version}
            {v.created_by ? ` — ${v.created_by}` : ""}
            {" · "}
            {formatRelativeTime(v.created_at)}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
