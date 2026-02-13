import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import ToolsPage from "@/app/(dashboard)/tools/page";

// Mock next/navigation
jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
  usePathname: () => "/tools",
  useParams: () => ({ tool: "valuation" }),
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

describe("ToolsPage", () => {
  test("renders all 9 tool cards", () => {
    render(<ToolsPage />);

    expect(screen.getByText("Startup Valuation")).toBeInTheDocument();
    expect(screen.getByText("Investor Readiness")).toBeInTheDocument();
    expect(screen.getByText("Scenario Modeler")).toBeInTheDocument();
    expect(screen.getByText("Benchmark Comparison")).toBeInTheDocument();
    expect(screen.getByText("Success Story Matcher")).toBeInTheDocument();
    expect(screen.getByText("AI Pitch Generator")).toBeInTheDocument();
    expect(screen.getByText("Founder Coach")).toBeInTheDocument();
    expect(screen.getByText("Expansion Advisor")).toBeInTheDocument();
    expect(screen.getByText("Fundraising Playbook")).toBeInTheDocument();
  });

  test("tool cards link to individual tool pages", () => {
    render(<ToolsPage />);

    const links = screen.getAllByRole("link");
    const toolLinks = links.filter((link) =>
      link.getAttribute("href")?.startsWith("/tools/")
    );
    expect(toolLinks.length).toBe(9);
  });
});
