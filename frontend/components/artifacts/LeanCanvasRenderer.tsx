"use client";

interface LeanCanvasContent {
  problem?: string[];
  solution?: string[];
  key_metrics?: string[];
  unique_value_proposition?: string;
  unfair_advantage?: string;
  channels?: string[];
  customer_segments?: string[];
  cost_structure?: string[];
  revenue_streams?: string[];
}

interface LeanCanvasRendererProps {
  content: Record<string, unknown>;
}

function CanvasBlock({
  title,
  items,
  className,
}: {
  title: string;
  items: string[] | string | undefined;
  className?: string;
}) {
  const list = Array.isArray(items)
    ? items
    : typeof items === "string"
      ? [items]
      : [];

  return (
    <div className={`border p-3 ${className ?? ""}`}>
      <h4 className="mb-2 text-xs font-semibold uppercase text-muted-foreground">
        {title}
      </h4>
      {list.length > 0 ? (
        <ul className="space-y-1 text-sm">
          {list.map((item, i) => (
            <li key={i}>{item}</li>
          ))}
        </ul>
      ) : (
        <p className="text-xs text-muted-foreground italic">Not defined</p>
      )}
    </div>
  );
}

export function LeanCanvasRenderer({ content }: LeanCanvasRendererProps) {
  const c = content as LeanCanvasContent;

  return (
    <div data-testid="lean-canvas" className="space-y-0">
      {/* Row 1: 2-3-2 layout */}
      <div className="grid grid-cols-1 md:grid-cols-5">
        <div className="md:col-span-1">
          <CanvasBlock
            title="Problem"
            items={c.problem}
            className="h-full"
          />
        </div>
        <div className="md:col-span-1">
          <CanvasBlock
            title="Solution"
            items={c.solution}
            className="h-full"
          />
        </div>
        <div className="md:col-span-1">
          <CanvasBlock
            title="Unique Value Proposition"
            items={c.unique_value_proposition}
            className="h-full"
          />
        </div>
        <div className="md:col-span-1">
          <CanvasBlock
            title="Unfair Advantage"
            items={c.unfair_advantage}
            className="h-full"
          />
        </div>
        <div className="md:col-span-1">
          <CanvasBlock
            title="Customer Segments"
            items={c.customer_segments}
            className="h-full"
          />
        </div>
      </div>
      {/* Row 2 */}
      <div className="grid grid-cols-1 md:grid-cols-3">
        <CanvasBlock title="Key Metrics" items={c.key_metrics} />
        <CanvasBlock title="Channels" items={c.channels} />
        <CanvasBlock title="Revenue Streams" items={c.revenue_streams} />
      </div>
      {/* Row 3 */}
      <div className="grid grid-cols-1 md:grid-cols-1">
        <CanvasBlock title="Cost Structure" items={c.cost_structure} />
      </div>
    </div>
  );
}
