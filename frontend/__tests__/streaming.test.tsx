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
});
