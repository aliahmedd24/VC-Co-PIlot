import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { EntityTypeSection } from "@/components/profile/EntityTypeSection";
import { EntityCard } from "@/components/profile/EntityCard";
import { KGEntityType, KGEntityStatus } from "@/lib/types";
import type { EntityResult } from "@/lib/types";

// Mock next/navigation
jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
  usePathname: () => "/profile",
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

const mockEntities: EntityResult[] = [
  {
    id: "entity-1",
    type: KGEntityType.MARKET,
    status: KGEntityStatus.CONFIRMED,
    data: { name: "Enterprise SaaS", tam: "$50B", growth_rate: "15%" },
    confidence: 0.85,
    evidence_count: 3,
  },
  {
    id: "entity-2",
    type: KGEntityType.MARKET,
    status: KGEntityStatus.SUGGESTED,
    data: { name: "SMB Tools", tam: "$10B" },
    confidence: 0.45,
    evidence_count: 1,
  },
  {
    id: "entity-3",
    type: KGEntityType.COMPETITOR,
    status: KGEntityStatus.NEEDS_REVIEW,
    data: { name: "CompetitorX", funding: "$20M" },
    confidence: 0.6,
    evidence_count: 2,
  },
];

describe("EntityTypeSection", () => {
  test("renders entities grouped by type with count badge", () => {
    const marketEntities = mockEntities.filter(
      (e) => e.type === KGEntityType.MARKET
    );

    render(
      <EntityTypeSection
        type={KGEntityType.MARKET}
        entities={marketEntities}
        onUpdate={jest.fn()}
        onDelete={jest.fn()}
      />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText("Market")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument(); // count badge
    expect(screen.getByText("Enterprise SaaS")).toBeInTheDocument();
    expect(screen.getByText("SMB Tools")).toBeInTheDocument();
  });
});

describe("EntityCard", () => {
  test("confirm button calls onUpdate with confirmed status", async () => {
    const user = userEvent.setup();
    const onUpdate = jest.fn();

    render(
      <EntityCard
        entity={mockEntities[1]} // Suggested entity
        onUpdate={onUpdate}
        onDelete={jest.fn()}
      />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText("Suggested")).toBeInTheDocument();
    expect(screen.getByText("SMB Tools")).toBeInTheDocument();

    const confirmBtn = screen.getByTestId("confirm-entity-btn");
    await user.click(confirmBtn);

    expect(onUpdate).toHaveBeenCalledWith("entity-2", {
      status: KGEntityStatus.CONFIRMED,
    });
  });

  test("renders entity data fields and confidence", () => {
    render(
      <EntityCard
        entity={mockEntities[0]}
        onUpdate={jest.fn()}
        onDelete={jest.fn()}
      />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText("Confirmed")).toBeInTheDocument();
    expect(screen.getByText("Enterprise SaaS")).toBeInTheDocument();
    expect(screen.getByText("$50B")).toBeInTheDocument();
    expect(screen.getByText("High (85%)")).toBeInTheDocument();
    expect(screen.getByText("3 evidence")).toBeInTheDocument();
  });
});
