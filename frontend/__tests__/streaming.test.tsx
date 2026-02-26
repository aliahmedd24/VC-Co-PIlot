import { render, screen } from "@testing-library/react";
import { StreamingMessage } from "@/components/chat/StreamingMessage";
import type { SSERoutingEvent, ModelProfile } from "@/lib/types";

// Mock next/navigation
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() }),
  usePathname: () => "/chat",
}));

// Mock next/link
jest.mock("next/link", () => {
  return function MockLink({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) {
    return <a href={href}>{children}</a>;
  };
});

const mockRoutingEvent: SSERoutingEvent = {
  selected_agent: "venture-architect",
  model_profile: "default" as ModelProfile,
  tools: [],
  artifact_needed: false,
  fallback_agent: "venture-architect",
  confidence: 0.85,
  reasoning: "Test routing",
  latency_ms: 15,
};

describe("StreamingMessage", () => {
  test("shows agent name from routing event", () => {
    render(
      <StreamingMessage
        content="Hello world"
        routingEvent={mockRoutingEvent}
      />
    );

    expect(screen.getByText("Venture Architect")).toBeInTheDocument();
    expect(screen.getByText(/Hello world/)).toBeInTheDocument();
  });

  test("shows loading indicator when content is empty", () => {
    render(<StreamingMessage content="" routingEvent={mockRoutingEvent} />);

    expect(screen.getByText("Generating...")).toBeInTheDocument();
  });

  test("shows active tool indicators", () => {
    render(
      <StreamingMessage
        content=""
        routingEvent={mockRoutingEvent}
        activeTools={["run_valuation"]}
        toolResults={[]}
      />
    );

    // Should show tool activity area
    expect(screen.getByTestId("tool-activity")).toBeInTheDocument();
    // Active tool pill should be rendered
    expect(screen.getByTestId("tool-active-run_valuation")).toBeInTheDocument();
    // Should display gerund-form label
    expect(screen.getByText("Running Valuation")).toBeInTheDocument();
    // Loading text should reference the tool
    expect(screen.getByText("Using Running Valuation...")).toBeInTheDocument();
  });

  test("shows completed tool results", () => {
    render(
      <StreamingMessage
        content="Analysis complete"
        routingEvent={mockRoutingEvent}
        activeTools={[]}
        toolResults={["score_readiness", "run_valuation"]}
      />
    );

    // Completed tool pills should be rendered
    expect(screen.getByTestId("tool-done-score_readiness")).toBeInTheDocument();
    expect(screen.getByTestId("tool-done-run_valuation")).toBeInTheDocument();
    expect(screen.getByText("Scoring Readiness")).toBeInTheDocument();
    expect(screen.getByText("Running Valuation")).toBeInTheDocument();
  });

  test("shows both active and completed tools simultaneously", () => {
    render(
      <StreamingMessage
        content="Working on it..."
        routingEvent={mockRoutingEvent}
        activeTools={["search_brain"]}
        toolResults={["query_entities"]}
      />
    );

    expect(screen.getByTestId("tool-active-search_brain")).toBeInTheDocument();
    expect(screen.getByTestId("tool-done-query_entities")).toBeInTheDocument();
  });
});
