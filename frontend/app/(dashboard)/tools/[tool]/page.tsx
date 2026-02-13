"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";
import { ValuationTool } from "@/components/tools/ValuationTool";
import { ReadinessScoreCard } from "@/components/tools/ReadinessScoreCard";
import { ScenarioModeler } from "@/components/tools/ScenarioModeler";
import { BenchmarkComparison } from "@/components/tools/BenchmarkComparison";
import { SuccessStoryMatcher } from "@/components/tools/SuccessStoryMatcher";
import { PitchGenerator } from "@/components/tools/PitchGenerator";
import { FounderCoach } from "@/components/tools/FounderCoach";
import { ExpansionAdvisor } from "@/components/tools/ExpansionAdvisor";
import { FundraisingPlaybook } from "@/components/tools/FundraisingPlaybook";

const TOOL_MAP: Record<string, { name: string; component: React.ComponentType }> = {
  valuation: { name: "Startup Valuation", component: ValuationTool },
  readiness: { name: "Investor Readiness Score", component: ReadinessScoreCard },
  scenarios: { name: "Scenario Modeler", component: ScenarioModeler },
  benchmarks: { name: "Benchmark Comparison", component: BenchmarkComparison },
  "success-stories": { name: "Success Story Matcher", component: SuccessStoryMatcher },
  pitch: { name: "AI Pitch Generator", component: PitchGenerator },
  coach: { name: "Founder Coach", component: FounderCoach },
  expansion: { name: "Expansion Advisor", component: ExpansionAdvisor },
  playbook: { name: "Fundraising Playbook", component: FundraisingPlaybook },
};

export default function ToolPage() {
  const params = useParams();
  const toolId = params.tool as string;
  const tool = TOOL_MAP[toolId];

  if (!tool) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <h2 className="text-lg font-semibold">Tool not found</h2>
        <Link href="/tools">
          <Button variant="link">Back to Tools</Button>
        </Link>
      </div>
    );
  }

  const ToolComponent = tool.component;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/tools">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="mr-1 h-4 w-4" />
            Back
          </Button>
        </Link>
        <h2 className="text-2xl font-bold tracking-tight">{tool.name}</h2>
      </div>

      <ToolComponent />
    </div>
  );
}
