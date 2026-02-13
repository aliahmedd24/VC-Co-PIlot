import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { DocumentList } from "@/components/documents/DocumentList";
import { DocumentStatus, DocumentType } from "@/lib/types";
import type { Document } from "@/lib/types";

// Mock next/navigation
jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
  usePathname: () => "/documents",
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

const mockDocuments: Document[] = [
  {
    id: "doc-1",
    name: "pitch-deck.pdf",
    type: DocumentType.PITCH_DECK,
    status: DocumentStatus.INDEXED,
    mime_type: "application/pdf",
    size: 2400000,
    created_at: new Date().toISOString(),
  },
  {
    id: "doc-2",
    name: "financials.xlsx",
    type: DocumentType.FINANCIAL_MODEL,
    status: DocumentStatus.PROCESSING,
    mime_type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    size: 1500000,
    created_at: new Date().toISOString(),
  },
];

describe("DocumentList", () => {
  test("renders documents with names and status badges", () => {
    render(
      <DocumentList documents={mockDocuments} isLoading={false} />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText("pitch-deck.pdf")).toBeInTheDocument();
    expect(screen.getByText("financials.xlsx")).toBeInTheDocument();
    expect(screen.getByText("Indexed")).toBeInTheDocument();
    expect(screen.getByText("Processing")).toBeInTheDocument();
  });

  test("shows empty state when no documents", () => {
    render(
      <DocumentList documents={[]} isLoading={false} />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText("No documents yet")).toBeInTheDocument();
    expect(
      screen.getByText("Upload your first document above.")
    ).toBeInTheDocument();
  });
});
