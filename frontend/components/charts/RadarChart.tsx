"use client";

import {
  RadarChart as RechartsRadar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

interface RadarDataPoint {
  subject: string;
  value: number;
  fullMark: number;
}

interface RadarChartProps {
  data: RadarDataPoint[];
  className?: string;
}

export function RadarChart({ data, className }: RadarChartProps) {
  return (
    <div data-testid="radar-chart" className={className}>
      <ResponsiveContainer width="100%" height={300}>
        <RechartsRadar cx="50%" cy="50%" outerRadius="80%" data={data}>
          <PolarGrid />
          <PolarAngleAxis dataKey="subject" className="text-xs" />
          <PolarRadiusAxis angle={30} domain={[0, 100]} />
          <Radar
            name="Score"
            dataKey="value"
            stroke="hsl(var(--primary))"
            fill="hsl(var(--primary))"
            fillOpacity={0.3}
          />
          <Tooltip />
        </RechartsRadar>
      </ResponsiveContainer>
    </div>
  );
}
