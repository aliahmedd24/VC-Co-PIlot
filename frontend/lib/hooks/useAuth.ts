import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { login, register, getMe } from "@/lib/api/auth";
import { useAuthStore } from "@/lib/stores/authStore";
import { toast } from "@/lib/hooks/useToast";

export function useLogin() {
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);

  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      login(email, password),
    onSuccess: async (data) => {
      localStorage.setItem("access_token", data.access_token);
      try {
        const user = await getMe();
        setAuth(user, data.access_token);
      } catch {
        // Token is valid but /me failed — set token anyway
        useAuthStore.getState().loadFromStorage();
      }
      router.push("/chat");
    },
    onError: () => {
      toast({
        variant: "destructive",
        title: "Login failed",
        description: "Invalid email or password.",
      });
    },
  });
}

export function useRegister() {
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);

  return useMutation({
    mutationFn: ({
      email,
      password,
      name,
    }: {
      email: string;
      password: string;
      name?: string;
    }) => register(email, password, name),
    onSuccess: async (data) => {
      localStorage.setItem("access_token", data.access_token);
      try {
        const user = await getMe();
        setAuth(user, data.access_token);
      } catch {
        useAuthStore.getState().loadFromStorage();
      }
      router.push("/onboarding");
    },
    onError: () => {
      toast({
        variant: "destructive",
        title: "Registration failed",
        description: "Could not create account. Email may already be in use.",
      });
    },
  });
}

export function useCurrentUser() {
  const setAuth = useAuthStore((s) => s.setAuth);
  const token = useAuthStore((s) => s.token);

  return useQuery({
    queryKey: ["currentUser"],
    queryFn: async () => {
      const user = await getMe();
      if (token) {
        setAuth(user, token);
      }
      return user;
    },
    enabled: !!token,
    retry: false,
  });
}

export function useLogout() {
  const router = useRouter();
  const clearAuth = useAuthStore((s) => s.clearAuth);
  const queryClient = useQueryClient();

  return () => {
    clearAuth();
    queryClient.clear();
    router.push("/login");
  };
}
