"use client";

import { Badge } from "@/components/ui/badge";
import type { ArtifactVersion } from "@/lib/types";

interface VersionDiffProps {
  versionA: ArtifactVersion;
  versionB: ArtifactVersion;
}

interface DiffChange {
  path: string;
  action: "added" | "removed" | "changed";
  oldValue?: string;
  newValue?: string;
}

function parseDiff(diff: Record<string, unknown> | null): DiffChange[] {
  if (!diff) return [];
  const changes: DiffChange[] = [];

  const added = diff["dictionary_item_added"] as string[] | undefined;
  if (Array.isArray(added)) {
    for (const path of added) {
      changes.push({ path, action: "added" });
    }
  }

  const removed = diff["dictionary_item_removed"] as string[] | undefined;
  if (Array.isArray(removed)) {
    for (const path of removed) {
      changes.push({ path, action: "removed" });
    }
  }

  const changed = diff["values_changed"] as Record<
    string,
    { old_value?: unknown; new_value?: unknown }
  > | undefined;
  if (changed && typeof changed === "object") {
    for (const [path, vals] of Object.entries(changed)) {
      changes.push({
        path,
        action: "changed",
        oldValue: String(vals.old_value ?? ""),
        newValue: String(vals.new_value ?? ""),
      });
    }
  }

  return changes;
}

function actionBadge(action: DiffChange["action"]) {
  switch (action) {
    case "added":
      return (
        <Badge className="bg-green-600 hover:bg-green-700 text-white text-[10px]">
          Added
        </Badge>
      );
    case "removed":
      return (
        <Badge variant="destructive" className="text-[10px]">
          Removed
        </Badge>
      );
    case "changed":
      return (
        <Badge variant="default" className="text-[10px]">
          Changed
        </Badge>
      );
  }
}

export function VersionDiff({ versionA, versionB }: VersionDiffProps) {
  const later =
    versionA.version > versionB.version ? versionA : versionB;
  const changes = parseDiff(later.diff);

  if (changes.length === 0) {
    return (
      <div className="py-8 text-center text-sm text-muted-foreground">
        No differences found between v{versionA.version} and v
        {versionB.version}.
      </div>
    );
  }

  return (
    <div data-testid="version-diff" className="space-y-3">
      <h4 className="text-sm font-semibold">
        Changes from v{Math.min(versionA.version, versionB.version)} to v
        {Math.max(versionA.version, versionB.version)}
      </h4>
      <div className="space-y-2">
        {changes.map((change, i) => (
          <div
            key={i}
            className="rounded border p-3"
            data-testid="diff-change"
          >
            <div className="flex items-center gap-2">
              {actionBadge(change.action)}
              <code className="text-xs text-muted-foreground">
                {change.path}
              </code>
            </div>
            {change.action === "changed" && (
              <div className="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-2">
                <div className="rounded bg-red-50 p-2 dark:bg-red-950/20">
                  <p className="mb-1 text-[10px] font-semibold text-red-600">
                    Before
                  </p>
                  <p className="text-xs break-all">{change.oldValue}</p>
                </div>
                <div className="rounded bg-green-50 p-2 dark:bg-green-950/20">
                  <p className="mb-1 text-[10px] font-semibold text-green-600">
                    After
                  </p>
                  <p className="text-xs break-all">{change.newValue}</p>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
