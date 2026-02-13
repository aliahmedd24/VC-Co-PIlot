"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

interface WaterfallDataPoint {
  name: string;
  value: number;
  color?: string;
}

interface WaterfallChartProps {
  data: WaterfallDataPoint[];
  className?: string;
}

const COLORS = [
  "hsl(var(--primary))",
  "hsl(210, 70%, 55%)",
  "hsl(190, 70%, 50%)",
  "hsl(160, 60%, 45%)",
  "hsl(140, 60%, 40%)",
];

export function WaterfallChart({ data, className }: WaterfallChartProps) {
  return (
    <div data-testid="waterfall-chart" className={className}>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" className="text-xs" />
          <YAxis className="text-xs" />
          <Tooltip
            formatter={(value: number) => `${value.toFixed(1)}%`}
          />
          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
            {data.map((_, index) => (
              <Cell
                key={`cell-${index}`}
                fill={COLORS[index % COLORS.length]}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
