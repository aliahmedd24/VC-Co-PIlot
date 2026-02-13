"use client";

import { Presentation } from "lucide-react";

interface Slide {
  title?: string;
  content?: string;
  notes?: string;
  order?: number;
}

interface DeckOutlineContent {
  title?: string;
  slides?: Slide[];
  narrative_arc?: string;
}

interface DeckOutlineRendererProps {
  content: Record<string, unknown>;
}

export function DeckOutlineRenderer({ content }: DeckOutlineRendererProps) {
  const c = content as DeckOutlineContent;
  const slides = c.slides ?? [];

  return (
    <div data-testid="deck-outline" className="space-y-4">
      {c.title && (
        <h3 className="text-lg font-semibold">{c.title}</h3>
      )}
      {c.narrative_arc && (
        <p className="text-sm text-muted-foreground italic">
          {c.narrative_arc}
        </p>
      )}
      <div className="space-y-3">
        {slides.map((slide, i) => (
          <div
            key={i}
            className="flex gap-3 rounded-lg border p-3"
            data-testid="slide-item"
          >
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-muted text-xs font-semibold">
              {slide.order ?? i + 1}
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <Presentation className="h-4 w-4 text-orange-600" />
                <h4 className="font-medium">
                  {slide.title ?? `Slide ${i + 1}`}
                </h4>
              </div>
              {slide.content && (
                <p className="mt-1 text-sm text-muted-foreground">
                  {slide.content}
                </p>
              )}
              {slide.notes && (
                <p className="mt-1 text-xs italic text-muted-foreground">
                  Notes: {slide.notes}
                </p>
              )}
            </div>
          </div>
        ))}
        {slides.length === 0 && (
          <p className="text-sm text-muted-foreground italic">
            No slides defined yet.
          </p>
        )}
      </div>
    </div>
  );
}
