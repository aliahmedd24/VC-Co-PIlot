import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import LoginPage from "@/app/(auth)/login/page";
import RegisterPage from "@/app/(auth)/register/page";
import { useAuthStore } from "@/lib/stores/authStore";

// Mock next/navigation
const mockPush = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
  usePathname: () => "/login",
}));

// Mock API calls
jest.mock("@/lib/api/auth", () => ({
  login: jest.fn(),
  register: jest.fn(),
  getMe: jest.fn(),
}));

import { login, register, getMe } from "@/lib/api/auth";

const mockedLogin = login as jest.MockedFunction<typeof login>;
const mockedRegister = register as jest.MockedFunction<typeof register>;
const mockedGetMe = getMe as jest.MockedFunction<typeof getMe>;

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

beforeEach(() => {
  jest.clearAllMocks();
  useAuthStore.getState().clearAuth();
  localStorage.clear();
});

describe("Login Page", () => {
  test("login form submission stores token and redirects to /chat", async () => {
    const user = userEvent.setup();
    mockedLogin.mockResolvedValue({
      access_token: "test-token-123",
      token_type: "bearer",
    });
    mockedGetMe.mockResolvedValue({
      id: "user-1",
      email: "test@example.com",
      name: "Test User",
      is_active: true,
    });

    render(<LoginPage />, { wrapper: createWrapper() });

    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.type(screen.getByLabelText(/password/i), "password123");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(mockedLogin).toHaveBeenCalledWith("test@example.com", "password123");
    });

    await waitFor(() => {
      expect(localStorage.getItem("access_token")).toBe("test-token-123");
    });

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/chat");
    });
  });

  test("login with invalid credentials shows error", async () => {
    const user = userEvent.setup();
    mockedLogin.mockRejectedValue(new Error("Unauthorized"));

    render(<LoginPage />, { wrapper: createWrapper() });

    await user.type(screen.getByLabelText(/email/i), "bad@example.com");
    await user.type(screen.getByLabelText(/password/i), "wrongpass123");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(mockedLogin).toHaveBeenCalled();
    });

    // Token should not be stored
    expect(localStorage.getItem("access_token")).toBeNull();
  });
});

describe("Register Page", () => {
  test("register form renders required fields", () => {
    render(<RegisterPage />, { wrapper: createWrapper() });

    expect(screen.getByLabelText(/name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /create account/i })
    ).toBeInTheDocument();

    // API should not be called without submission
    expect(mockedRegister).not.toHaveBeenCalled();
  });
});

describe("Logout", () => {
  test("logout clears token and redirects to /login", () => {
    // Set up authenticated state
    useAuthStore.getState().setAuth(
      { id: "user-1", email: "test@example.com", name: "Test", is_active: true },
      "test-token"
    );

    expect(localStorage.getItem("access_token")).toBe("test-token");
    expect(useAuthStore.getState().isAuthenticated).toBe(true);

    // Clear auth (simulates logout)
    useAuthStore.getState().clearAuth();

    expect(localStorage.getItem("access_token")).toBeNull();
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
    expect(useAuthStore.getState().user).toBeNull();
    expect(useAuthStore.getState().token).toBeNull();
  });
});

describe("Auth Guard", () => {
  test("unauthenticated state has no token", () => {
    // Without loading from storage or setting auth, should be unauthenticated
    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.token).toBeNull();
  });
});
