"use client";

import { useState } from "react";
import { Pencil, Check, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { VentureStage } from "@/lib/types";
import type { Venture, VentureUpdateRequest } from "@/lib/types";

interface VentureHeaderProps {
  venture: Venture;
  workspaceId: string;
  onUpdate: (updates: VentureUpdateRequest) => void;
  isUpdating: boolean;
}

function stageName(stage: VentureStage): string {
  return stage
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

export function VentureHeader({
  venture,
  workspaceId,
  onUpdate,
  isUpdating,
}: VentureHeaderProps) {
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(venture.name);
  const [stage, setStage] = useState(venture.stage);
  const [oneLiner, setOneLiner] = useState(venture.one_liner ?? "");
  const [problem, setProblem] = useState(venture.problem ?? "");
  const [solution, setSolution] = useState(venture.solution ?? "");

  function handleSave() {
    onUpdate({
      name: name !== venture.name ? name : undefined,
      stage: stage !== venture.stage ? stage : undefined,
      one_liner: oneLiner !== (venture.one_liner ?? "") ? oneLiner : undefined,
      problem: problem !== (venture.problem ?? "") ? problem : undefined,
      solution: solution !== (venture.solution ?? "") ? solution : undefined,
    });
    setEditing(false);
  }

  function handleCancel() {
    setName(venture.name);
    setStage(venture.stage);
    setOneLiner(venture.one_liner ?? "");
    setProblem(venture.problem ?? "");
    setSolution(venture.solution ?? "");
    setEditing(false);
  }

  return (
    <div className="rounded-lg border p-4 sm:p-6" data-testid="venture-header">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          {editing ? (
            <div className="space-y-3">
              <div>
                <label className="text-xs font-medium text-muted-foreground">
                  Name
                </label>
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="mt-1"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">
                  Stage
                </label>
                <Select
                  value={stage}
                  onValueChange={(v) => setStage(v as VentureStage)}
                >
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.values(VentureStage).map((s) => (
                      <SelectItem key={s} value={s}>
                        {stageName(s)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">
                  One-liner
                </label>
                <Input
                  value={oneLiner}
                  onChange={(e) => setOneLiner(e.target.value)}
                  placeholder="Describe your venture in one sentence"
                  className="mt-1"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">
                  Problem
                </label>
                <Textarea
                  value={problem}
                  onChange={(e) => setProblem(e.target.value)}
                  placeholder="What problem does your venture solve?"
                  className="mt-1 min-h-[60px]"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">
                  Solution
                </label>
                <Textarea
                  value={solution}
                  onChange={(e) => setSolution(e.target.value)}
                  placeholder="How does your venture solve this problem?"
                  className="mt-1 min-h-[60px]"
                />
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  onClick={handleSave}
                  disabled={isUpdating}
                >
                  <Check className="mr-1 h-3 w-3" />
                  Save
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleCancel}
                >
                  <X className="mr-1 h-3 w-3" />
                  Cancel
                </Button>
              </div>
            </div>
          ) : (
            <div>
              <div className="flex items-center gap-3">
                <h2 className="text-xl font-bold">{venture.name}</h2>
                <Badge variant="outline">{stageName(venture.stage)}</Badge>
              </div>
              {venture.one_liner && (
                <p className="mt-1 text-sm text-muted-foreground">
                  {venture.one_liner}
                </p>
              )}
              {venture.problem && (
                <div className="mt-3">
                  <h4 className="text-xs font-semibold uppercase text-muted-foreground">
                    Problem
                  </h4>
                  <p className="text-sm">{venture.problem}</p>
                </div>
              )}
              {venture.solution && (
                <div className="mt-2">
                  <h4 className="text-xs font-semibold uppercase text-muted-foreground">
                    Solution
                  </h4>
                  <p className="text-sm">{venture.solution}</p>
                </div>
              )}
            </div>
          )}
        </div>
        {!editing && (
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setEditing(true)}
            data-testid="edit-venture-btn"
          >
            <Pencil className="h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  );
}
