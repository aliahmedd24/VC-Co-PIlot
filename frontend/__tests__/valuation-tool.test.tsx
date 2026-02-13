import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ValuationTool } from "@/components/tools/ValuationTool";

// Mock next/navigation
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() }),
  usePathname: () => "/tools/valuation",
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

describe("ValuationTool", () => {
  test("renders input fields", () => {
    render(<ValuationTool />, { wrapper: createWrapper() });

    expect(screen.getByLabelText(/Annual Revenue/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Growth Rate/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Industry/i)).toBeInTheDocument();
  });

  test("renders calculate button", () => {
    render(<ValuationTool />, { wrapper: createWrapper() });

    expect(
      screen.getByRole("button", { name: /Calculate Valuation/i })
    ).toBeInTheDocument();
  });
});
