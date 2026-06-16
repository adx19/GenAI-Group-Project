"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Sparkles, BarChart3, Search } from "lucide-react";
import { cn } from "@/lib/utils";

const links = [
  { href: "/", label: "Discover", icon: Search },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
];

export function Navbar() {
  const pathname = usePathname();
  return (
    <header className="sticky top-0 z-40 w-full border-b bg-background/70 backdrop-blur">
      <div className="container flex h-16 items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-fuchsia-500 text-white shadow-md">
            <Sparkles className="h-4 w-4" />
          </div>
          <div className="leading-tight">
            <div className="text-sm font-semibold">Catalogue IQ</div>
            <div className="text-[10px] uppercase tracking-wider text-muted-foreground">
              Multimodal Discovery
            </div>
          </div>
        </Link>
        <nav className="flex items-center gap-1">
          {links.map((l) => {
            const Icon = l.icon;
            const active = pathname === l.href;
            return (
              <Link
                key={l.href}
                href={l.href}
                className={cn(
                  "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  active
                    ? "bg-accent text-accent-foreground"
                    : "text-muted-foreground hover:text-foreground hover:bg-accent/50",
                )}
              >
                <Icon className="h-4 w-4" />
                {l.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
