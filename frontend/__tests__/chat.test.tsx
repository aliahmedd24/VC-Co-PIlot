import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { MessageInput } from "@/components/chat/MessageInput";
import { ChatSidebar } from "@/components/chat/ChatSidebar";
import { MessageRole } from "@/lib/types";
import type { ChatMessage, ChatSession } from "@/lib/types";

// Mock next/navigation
jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
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

const mockUserMessage: ChatMessage = {
  id: "msg-1",
  role: MessageRole.USER,
  content: "What is my market size?",
  agent_id: null,
  citations: null,
  artifact_id: null,
  created_at: new Date().toISOString(),
};

const mockAssistantMessage: ChatMessage = {
  id: "msg-2",
  role: MessageRole.ASSISTANT,
  content: "Based on my analysis, your total addressable market is $5B.",
  agent_id: "venture-architect",
  citations: null,
  artifact_id: null,
  created_at: new Date().toISOString(),
};

const mockSessions: ChatSession[] = [
  {
    id: "session-1",
    title: "Market Analysis Discussion",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    messages: [],
  },
  {
    id: "session-2",
    title: "Pitch Deck Review",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    messages: [],
  },
];

describe("ChatSidebar", () => {
  test("renders session list with titles", () => {
    render(
      <ChatSidebar
        sessions={mockSessions}
        activeSessionId={null}
        onSelectSession={jest.fn()}
        onNewChat={jest.fn()}
        isLoading={false}
      />
    );

    expect(screen.getByText("Market Analysis Discussion")).toBeInTheDocument();
    expect(screen.getByText("Pitch Deck Review")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /new chat/i })
    ).toBeInTheDocument();
  });

  test("new chat button calls onNewChat", async () => {
    const user = userEvent.setup();
    const onNewChat = jest.fn();

    render(
      <ChatSidebar
        sessions={mockSessions}
        activeSessionId={null}
        onSelectSession={jest.fn()}
        onNewChat={onNewChat}
        isLoading={false}
      />
    );

    await user.click(screen.getByRole("button", { name: /new chat/i }));
    expect(onNewChat).toHaveBeenCalled();
  });
});

describe("MessageBubble", () => {
  test("renders user message content", () => {
    render(<MessageBubble message={mockUserMessage} />);

    expect(screen.getByText("What is my market size?")).toBeInTheDocument();
    // User messages should not show agent badge
    expect(screen.queryByText("Venture Architect")).not.toBeInTheDocument();
  });

  test("renders assistant message with agent badge", () => {
    render(<MessageBubble message={mockAssistantMessage} />);

    expect(
      screen.getByText(
        "Based on my analysis, your total addressable market is $5B."
      )
    ).toBeInTheDocument();
    expect(screen.getByText("Venture Architect")).toBeInTheDocument();
  });
});

describe("MessageInput", () => {
  test("sends message on Enter key", async () => {
    const user = userEvent.setup();
    const onSend = jest.fn();

    render(<MessageInput onSend={onSend} disabled={false} />, {
      wrapper: createWrapper(),
    });

    const textarea = screen.getByPlaceholderText(/type a message/i);
    await user.type(textarea, "Hello agent");
    await user.keyboard("{Enter}");

    await waitFor(() => {
      expect(onSend).toHaveBeenCalledWith("Hello agent", null);
    });
  });

  test("send button is disabled when input is empty", () => {
    render(<MessageInput onSend={jest.fn()} disabled={false} />, {
      wrapper: createWrapper(),
    });

    const sendButton = screen.getByRole("button", { name: /send message/i });
    expect(sendButton).toBeDisabled();
  });
});
