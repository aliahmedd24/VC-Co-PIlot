"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { VentureStage } from "@/lib/types";

const schema = z.object({
  name: z.string().min(1, "Venture name is required"),
  stage: z.nativeEnum(VentureStage),
  one_liner: z.string().max(500).optional(),
});

type FormData = z.infer<typeof schema>;

const stageLabels: Record<VentureStage, string> = {
  [VentureStage.IDEATION]: "Ideation",
  [VentureStage.PRE_SEED]: "Pre-Seed",
  [VentureStage.SEED]: "Seed",
  [VentureStage.SERIES_A]: "Series A",
  [VentureStage.SERIES_B]: "Series B",
  [VentureStage.GROWTH]: "Growth",
  [VentureStage.EXIT]: "Exit",
};

interface StepVentureProps {
  onNext: (data: FormData) => void;
  isPending: boolean;
}

export function StepVenture({ onNext, isPending }: StepVentureProps) {
  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      stage: VentureStage.IDEATION,
    },
  });

  return (
    <form onSubmit={handleSubmit(onNext)} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="venture-name">Venture Name</Label>
        <Input
          id="venture-name"
          placeholder="e.g., TechCo"
          {...register("name")}
        />
        {errors.name && (
          <p className="text-sm text-destructive">{errors.name.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label>Stage</Label>
        <Select
          defaultValue={VentureStage.IDEATION}
          onValueChange={(value) => setValue("stage", value as VentureStage)}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select stage" />
          </SelectTrigger>
          <SelectContent>
            {Object.entries(stageLabels).map(([value, label]) => (
              <SelectItem key={value} value={value}>
                {label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="one-liner">One-liner (optional)</Label>
        <Textarea
          id="one-liner"
          placeholder="Describe your venture in one sentence..."
          {...register("one_liner")}
          rows={2}
        />
      </div>

      <Button type="submit" className="w-full" disabled={isPending}>
        {isPending ? "Saving..." : "Continue"}
      </Button>
    </form>
  );
}
