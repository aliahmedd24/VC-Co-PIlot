"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/stores/authStore";
import { Button } from "@/components/ui/button";

export default function HomePage() {
  const router = useRouter();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const loadFromStorage = useAuthStore((s) => s.loadFromStorage);

  useEffect(() => {
    loadFromStorage();
  }, [loadFromStorage]);

  useEffect(() => {
    if (isAuthenticated) {
      router.push("/chat");
    }
  }, [isAuthenticated, router]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 p-4">
      <div className="text-center">
        <h1 className="text-4xl font-bold tracking-tight">AI VC Co-Pilot</h1>
        <p className="mt-2 text-lg text-muted-foreground">
          Your AI-powered startup advisory platform
        </p>
      </div>
      <div className="flex gap-4">
        <Button onClick={() => router.push("/login")}>Sign In</Button>
        <Button variant="outline" onClick={() => router.push("/register")}>
          Create Account
        </Button>
      </div>
    </div>
  );
}
