export interface AgentMeta {
  name: string;
  icon: string;
  color: string;
}

const agentMap: Record<string, AgentMeta> = {
  "venture-architect": {
    name: "Venture Architect",
    icon: "Compass",
    color: "text-blue-600",
  },
  "market-oracle": {
    name: "Market Oracle",
    icon: "TrendingUp",
    color: "text-green-600",
  },
  storyteller: {
    name: "Storyteller",
    icon: "BookOpen",
    color: "text-purple-600",
  },
  "deck-architect": {
    name: "Deck Architect",
    icon: "Presentation",
    color: "text-orange-600",
  },
  "valuation-strategist": {
    name: "Valuation Strategist",
    icon: "DollarSign",
    color: "text-emerald-600",
  },
  "lean-modeler": {
    name: "Lean Modeler",
    icon: "LayoutGrid",
    color: "text-cyan-600",
  },
  "kpi-dashboard": {
    name: "KPI Dashboard",
    icon: "BarChart3",
    color: "text-indigo-600",
  },
  "qa-simulator": {
    name: "Q&A Simulator",
    icon: "HelpCircle",
    color: "text-amber-600",
  },
  "dataroom-concierge": {
    name: "Dataroom Concierge",
    icon: "FolderOpen",
    color: "text-slate-600",
  },
  "icp-profiler": {
    name: "ICP Profiler",
    icon: "Users",
    color: "text-pink-600",
  },
  "pre-mortem-critic": {
    name: "Pre-Mortem Critic",
    icon: "AlertTriangle",
    color: "text-red-600",
  },
};

const defaultAgent: AgentMeta = {
  name: "Assistant",
  icon: "Bot",
  color: "text-gray-600",
};

export function getAgentMeta(agentId: string | null): AgentMeta {
  if (!agentId) return defaultAgent;
  return agentMap[agentId] ?? defaultAgent;
}

export function getAllAgents(): Array<{ id: string } & AgentMeta> {
  return Object.entries(agentMap).map(([id, meta]) => ({ id, ...meta }));
}
