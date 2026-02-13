"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const schema = z.object({
  name: z.string().min(1, "Workspace name is required").max(255),
});

type FormData = z.infer<typeof schema>;

interface StepWorkspaceProps {
  onNext: (name: string) => void;
  isPending: boolean;
}

export function StepWorkspace({ onNext, isPending }: StepWorkspaceProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  return (
    <form onSubmit={handleSubmit((data) => onNext(data.name))} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="workspace-name">Workspace Name</Label>
        <Input
          id="workspace-name"
          placeholder="e.g., My Startup"
          {...register("name")}
        />
        {errors.name && (
          <p className="text-sm text-destructive">{errors.name.message}</p>
        )}
      </div>
      <p className="text-sm text-muted-foreground">
        A workspace organizes all your documents, conversations, and artifacts
        for a single venture.
      </p>
      <Button type="submit" className="w-full" disabled={isPending}>
        {isPending ? "Creating..." : "Create Workspace"}
      </Button>
    </form>
  );
}
