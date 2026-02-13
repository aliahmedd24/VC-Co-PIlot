import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ArtifactGrid } from "@/components/artifacts/ArtifactGrid";
import { ArtifactRenderer } from "@/components/artifacts/ArtifactRenderer";
import { ArtifactType, ArtifactStatus } from "@/lib/types";
import type { Artifact } from "@/lib/types";

// Mock next/navigation
jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
  usePathname: () => "/artifacts",
  useParams: () => ({ id: "artifact-1" }),
}));

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

const mockArtifacts: Artifact[] = [
  {
    id: "artifact-1",
    type: ArtifactType.LEAN_CANVAS,
    title: "SaaS Lean Canvas",
    status: ArtifactStatus.READY,
    owner_agent: "lean-modeler",
    content: {
      problem: ["High churn", "Low engagement"],
      solution: ["AI-powered retention"],
    },
    current_version: 3,
    assumptions: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "artifact-2",
    type: ArtifactType.DECK_OUTLINE,
    title: "Series A Pitch Deck",
    status: ArtifactStatus.IN_PROGRESS,
    owner_agent: "deck-architect",
    content: {
      slides: [
        { title: "Problem", content: "Market pain points", order: 1 },
        { title: "Solution", content: "Our approach", order: 2 },
      ],
    },
    current_version: 1,
    assumptions: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "artifact-3",
    type: ArtifactType.FINANCIAL_MODEL,
    title: "Revenue Projection",
    status: ArtifactStatus.DRAFT,
    owner_agent: "valuation-strategist",
    content: {},
    current_version: 1,
    assumptions: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

describe("ArtifactGrid", () => {
  test("renders artifact cards with type, title, and status", () => {
    render(
      <ArtifactGrid
        artifacts={mockArtifacts}
        isLoading={false}
        onSelect={jest.fn()}
      />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText("SaaS Lean Canvas")).toBeInTheDocument();
    expect(screen.getByText("Series A Pitch Deck")).toBeInTheDocument();
    expect(screen.getByText("Revenue Projection")).toBeInTheDocument();
    expect(screen.getByText("Ready")).toBeInTheDocument();
    expect(screen.getByText("In Progress")).toBeInTheDocument();
    expect(screen.getByText("Draft")).toBeInTheDocument();
    expect(screen.getByText("Lean Canvas")).toBeInTheDocument();
    expect(screen.getByText("Deck Outline")).toBeInTheDocument();
  });

  test("calls onSelect when artifact card is clicked", async () => {
    const user = userEvent.setup();
    const onSelect = jest.fn();

    render(
      <ArtifactGrid
        artifacts={mockArtifacts}
        isLoading={false}
        onSelect={onSelect}
      />,
      { wrapper: createWrapper() }
    );

    const cards = screen.getAllByTestId("artifact-card");
    await user.click(cards[0]);

    expect(onSelect).toHaveBeenCalledWith("artifact-1");
  });

  test("shows empty state when no artifacts", () => {
    render(
      <ArtifactGrid artifacts={[]} isLoading={false} onSelect={jest.fn()} />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText("No artifacts yet")).toBeInTheDocument();
  });
});

describe("ArtifactRenderer", () => {
  test("renders lean canvas with blocks", () => {
    render(
      <ArtifactRenderer
        type={ArtifactType.LEAN_CANVAS}
        content={{
          problem: ["High churn", "Low engagement"],
          solution: ["AI-powered retention"],
          unique_value_proposition: "Reduce churn by 50%",
          customer_segments: ["B2B SaaS companies"],
        }}
      />
    );

    expect(screen.getByTestId("lean-canvas")).toBeInTheDocument();
    expect(screen.getByText("High churn")).toBeInTheDocument();
    expect(screen.getByText("AI-powered retention")).toBeInTheDocument();
    expect(screen.getByText("Reduce churn by 50%")).toBeInTheDocument();
  });

  test("renders deck outline with slides", () => {
    render(
      <ArtifactRenderer
        type={ArtifactType.DECK_OUTLINE}
        content={{
          title: "Series A Deck",
          slides: [
            { title: "Problem Slide", content: "Market gap", order: 1 },
            { title: "Solution Slide", content: "Our product", order: 2 },
            { title: "Traction", content: "Growth metrics", order: 3 },
          ],
        }}
      />
    );

    expect(screen.getByTestId("deck-outline")).toBeInTheDocument();
    expect(screen.getByText("Problem Slide")).toBeInTheDocument();
    expect(screen.getByText("Solution Slide")).toBeInTheDocument();
    expect(screen.getByText("Traction")).toBeInTheDocument();
    const slides = screen.getAllByTestId("slide-item");
    expect(slides).toHaveLength(3);
  });
});
