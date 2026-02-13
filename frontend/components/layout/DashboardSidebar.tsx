"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  MessageSquare,
  FileBox,
  UserCircle,
  FileText,
  Settings,
  Wrench,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";

const navItems = [
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/tools", label: "Tools", icon: Wrench },
  { href: "/artifacts", label: "Artifacts", icon: FileBox },
  { href: "/profile", label: "Profile", icon: UserCircle },
  { href: "/documents", label: "Documents", icon: FileText },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function DashboardSidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden md:flex md:w-64 md:flex-col md:border-r md:bg-muted/40">
      <div className="flex h-14 items-center border-b px-4">
        <Link href="/chat" className="flex items-center gap-2 font-semibold">
          <span className="text-lg">AI VC Co-Pilot</span>
        </Link>
      </div>
      <nav className="flex-1 space-y-1 p-4">
        {navItems.map((item) => {
          const isActive = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
