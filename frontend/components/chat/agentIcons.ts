import type { LucideIcon } from "lucide-react";
import {
  Compass,
  TrendingUp,
  BookOpen,
  Presentation,
  DollarSign,
  LayoutGrid,
  BarChart3,
  HelpCircle,
  FolderOpen,
  Users,
  AlertTriangle,
  Bot,
} from "lucide-react";

const iconMap: Record<string, LucideIcon> = {
  Compass,
  TrendingUp,
  BookOpen,
  Presentation,
  DollarSign,
  LayoutGrid,
  BarChart3,
  HelpCircle,
  FolderOpen,
  Users,
  AlertTriangle,
  Bot,
};

export function resolveAgentIcon(iconName: string): LucideIcon {
  return iconMap[iconName] ?? Bot;
}
