"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  DollarSign,
  Shield,
  GitBranch,
  BarChart3,
  Star,
  Presentation,
  UserCircle,
  Globe,
  BookOpen,
} from "lucide-react";

const tools = [
  {
    id: "valuation",
    name: "Startup Valuation",
    description: "Calculate your startup valuation using revenue multiples, DCF, and comparables.",
    icon: DollarSign,
    color: "text-green-600",
  },
  {
    id: "readiness",
    name: "Investor Readiness",
    description: "Score your investor readiness across 5 dimensions with actionable recommendations.",
    icon: Shield,
    color: "text-blue-600",
  },
  {
    id: "scenarios",
    name: "Scenario Modeler",
    description: "Model funding rounds, dilution, cap table evolution, and exit scenarios.",
    icon: GitBranch,
    color: "text-purple-600",
  },
  {
    id: "benchmarks",
    name: "Benchmark Comparison",
    description: "Compare your metrics against peer cohorts and see your percentile ranking.",
    icon: BarChart3,
    color: "text-orange-600",
  },
  {
    id: "success-stories",
    name: "Success Story Matcher",
    description: "Find unicorns with similar attributes and learn from their journeys.",
    icon: Star,
    color: "text-yellow-600",
  },
  {
    id: "pitch",
    name: "AI Pitch Generator",
    description: "Generate a compelling pitch narrative tailored to your target audience.",
    icon: Presentation,
    color: "text-indigo-600",
  },
  {
    id: "coach",
    name: "Founder Coach",
    description: "Get personalized coaching on your founder positioning for investor meetings.",
    icon: UserCircle,
    color: "text-pink-600",
  },
  {
    id: "expansion",
    name: "Expansion Advisor",
    description: "Analyze cross-border expansion opportunities with market and regulatory insights.",
    icon: Globe,
    color: "text-teal-600",
  },
  {
    id: "playbook",
    name: "Fundraising Playbook",
    description: "Generate a complete fundraising playbook with timeline, checklists, and tips.",
    icon: BookOpen,
    color: "text-cyan-600",
  },
];

export default function ToolsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Tools</h2>
        <p className="text-muted-foreground">
          Specialized tools to help you prepare, analyze, and fundraise.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {tools.map((tool) => (
          <Link key={tool.id} href={`/tools/${tool.id}`}>
            <Card className="h-full transition-colors hover:bg-accent/50 cursor-pointer">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-sm">
                  <tool.icon className={`h-5 w-5 ${tool.color}`} />
                  {tool.name}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  {tool.description}
                </p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
