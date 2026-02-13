"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { StepWorkspace } from "@/components/onboarding/StepWorkspace";
import { StepVenture } from "@/components/onboarding/StepVenture";
import { StepDocument } from "@/components/onboarding/StepDocument";
import { useCreateWorkspace, useUpdateVenture } from "@/lib/hooks/useWorkspace";
import { useUploadDocument } from "@/lib/hooks/useDocuments";
import { useUIStore } from "@/lib/stores/uiStore";
import type { VentureStage } from "@/lib/types";

const steps = [
  { number: 1, title: "Create Workspace" },
  { number: 2, title: "Set Up Venture" },
  { number: 3, title: "Upload Document" },
];

export default function OnboardingPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [workspaceId, setWorkspaceId] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  const setActiveWorkspace = useUIStore((s) => s.setActiveWorkspace);
  const createWorkspace = useCreateWorkspace();
  const updateVenture = useUpdateVenture();
  const uploadDocument = useUploadDocument();

  const handleCreateWorkspace = (name: string) => {
    createWorkspace.mutate(name, {
      onSuccess: (workspace) => {
        setWorkspaceId(workspace.id);
        setActiveWorkspace(workspace.id);
        setCurrentStep(2);
      },
    });
  };

  const handleSetupVenture = (data: {
    name: string;
    stage: VentureStage;
    one_liner?: string;
  }) => {
    if (!workspaceId) return;
    updateVenture.mutate(
      {
        workspaceId,
        updates: {
          name: data.name,
          stage: data.stage,
          one_liner: data.one_liner ?? null,
        },
      },
      {
        onSuccess: () => {
          setCurrentStep(3);
        },
      }
    );
  };

  const handleUpload = (file: File) => {
    if (!workspaceId) return;
    uploadDocument.mutate(
      {
        workspaceId,
        file,
        onProgress: setUploadProgress,
      },
      {
        onSuccess: () => {
          router.push("/chat");
        },
      }
    );
  };

  const handleSkip = () => {
    router.push("/chat");
  };

  return (
    <div className="mx-auto max-w-lg py-8">
      {/* Progress indicator */}
      <div className="mb-8 flex items-center justify-center gap-4">
        {steps.map((step) => (
          <div key={step.number} className="flex items-center gap-2">
            <Badge
              variant={currentStep >= step.number ? "default" : "outline"}
              className="h-7 w-7 justify-center rounded-full p-0"
            >
              {step.number}
            </Badge>
            <span
              className={`hidden text-sm sm:inline ${
                currentStep >= step.number
                  ? "font-medium"
                  : "text-muted-foreground"
              }`}
            >
              {step.title}
            </span>
          </div>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>
            {steps[currentStep - 1].title}
          </CardTitle>
          <CardDescription>
            {currentStep === 1 &&
              "Start by creating a workspace for your venture."}
            {currentStep === 2 &&
              "Tell us about your venture so our AI agents can help."}
            {currentStep === 3 &&
              "Upload a document to get started, or skip for now."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {currentStep === 1 && (
            <StepWorkspace
              onNext={handleCreateWorkspace}
              isPending={createWorkspace.isPending}
            />
          )}
          {currentStep === 2 && (
            <StepVenture
              onNext={handleSetupVenture}
              isPending={updateVenture.isPending}
            />
          )}
          {currentStep === 3 && (
            <StepDocument
              onUpload={handleUpload}
              onSkip={handleSkip}
              isPending={uploadDocument.isPending}
              uploadProgress={uploadProgress}
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
