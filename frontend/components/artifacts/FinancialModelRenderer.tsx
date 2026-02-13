"use client";

interface FinancialRow {
  label?: string;
  values?: number[];
}

interface FinancialModelContent {
  title?: string;
  currency?: string;
  periods?: string[];
  revenue?: FinancialRow[];
  costs?: FinancialRow[];
  assumptions?: Record<string, unknown>;
  summary?: Record<string, unknown>;
}

interface FinancialModelRendererProps {
  content: Record<string, unknown>;
}

function formatCurrency(val: number, currency?: string): string {
  const c = currency ?? "USD";
  if (Math.abs(val) >= 1_000_000)
    return `${c === "USD" ? "$" : c}${(val / 1_000_000).toFixed(1)}M`;
  if (Math.abs(val) >= 1_000)
    return `${c === "USD" ? "$" : c}${(val / 1_000).toFixed(0)}K`;
  return `${c === "USD" ? "$" : c}${val.toFixed(0)}`;
}

function FinancialTable({
  title,
  rows,
  periods,
  currency,
}: {
  title: string;
  rows: FinancialRow[];
  periods: string[];
  currency?: string;
}) {
  return (
    <div className="space-y-2">
      <h4 className="text-sm font-semibold">{title}</h4>
      <div className="overflow-x-auto rounded border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="px-3 py-2 text-left font-medium">Item</th>
              {periods.map((p) => (
                <th key={p} className="px-3 py-2 text-right font-medium">
                  {p}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i} className="border-b last:border-0">
                <td className="px-3 py-2 font-medium">
                  {row.label ?? `Row ${i + 1}`}
                </td>
                {(row.values ?? []).map((val, j) => (
                  <td key={j} className="px-3 py-2 text-right tabular-nums">
                    {formatCurrency(val, currency)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function FinancialModelRenderer({
  content,
}: FinancialModelRendererProps) {
  const c = content as FinancialModelContent;
  const periods = c.periods ?? [];

  return (
    <div className="space-y-6">
      {c.title && <h3 className="text-lg font-semibold">{c.title}</h3>}

      {c.revenue && c.revenue.length > 0 && (
        <FinancialTable
          title="Revenue"
          rows={c.revenue}
          periods={periods}
          currency={c.currency}
        />
      )}

      {c.costs && c.costs.length > 0 && (
        <FinancialTable
          title="Costs"
          rows={c.costs}
          periods={periods}
          currency={c.currency}
        />
      )}

      {c.assumptions && Object.keys(c.assumptions).length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-semibold">Assumptions</h4>
          <div className="rounded border p-3">
            <dl className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {Object.entries(c.assumptions).map(([key, val]) => (
                <div key={key}>
                  <dt className="text-xs text-muted-foreground">
                    {key.replace(/_/g, " ")}
                  </dt>
                  <dd className="text-sm font-medium">{String(val)}</dd>
                </div>
              ))}
            </dl>
          </div>
        </div>
      )}
    </div>
  );
}
