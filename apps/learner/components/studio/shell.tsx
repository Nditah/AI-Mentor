"use client";

import { UserButton } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import {
  BookOpen,
  ClipboardCheck,
  FlaskConical,
  GraduationCap,
  LayoutDashboard,
  Map,
  MessageSquare,
  Search,
  Shield,
  SquareStack,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { api } from "@/lib/api";
import type { Dashboard } from "@/lib/types";
import { clerkEnabled } from "@/lib/csp";
import { cn, devAuth } from "@/lib/utils";
import { useStudio } from "@/stores/studio";
import { ThemeToggle } from "@/components/theme-toggle";

const links = [
  ["/dashboard", "Dashboard", LayoutDashboard],
  ["/tutor", "Tutor", MessageSquare],
  ["/quiz", "Quiz", ClipboardCheck],
  ["/paths", "Paths", GraduationCap],
  ["/catalog", "Catalog", Search],
  ["/graph", "Concept map", Map],
  ["/flashcards", "Flashcards", SquareStack],
  ["/lab", "Coding lab", FlaskConical],
  ["/research", "Research", BookOpen],
  ["/admin", "Admin", Shield],
] as const;

export function StudioShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const devUserId = useStudio((state) => state.devUserId);
  const setDevUserId = useStudio((state) => state.setDevUserId);
  const dashboard = useQuery({
    queryKey: ["dashboard", devUserId],
    queryFn: () => api<Dashboard>("/api/v1/dashboard"),
  });

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[240px_1fr]">
      <aside className="border-b border-slate-200 bg-white px-4 py-4 dark:border-slate-800 dark:bg-slate-950 lg:border-b-0 lg:border-r">
        <Link href="/" className="font-display text-2xl tracking-tight">
          AI Mentor
        </Link>
        <nav className="mt-4 flex gap-1 overflow-x-auto lg:flex-col" aria-label="Studio">
          {links.map(([href, label, Icon]) => {
            const active = pathname === href || pathname.startsWith(`${href}/`);
            return (
              <Link
                key={href}
                href={href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex items-center gap-2 rounded-full px-3 py-2 text-sm font-semibold",
                  active
                    ? "bg-[#1d4ed8] text-white"
                    : "text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800",
                )}
              >
                <Icon aria-hidden size={16} />
                {label}
              </Link>
            );
          })}
        </nav>
      </aside>
      <div>
        <header className="flex items-center justify-between gap-3 border-b border-slate-200 px-5 py-3 dark:border-slate-800">
          <p className="text-sm">
            {dashboard.data ? (
              <>
                <span className="font-semibold">{dashboard.data.display_name}</span>
                <span className="mx-2 text-slate-400">·</span>
                Level {dashboard.data.level}
                <span className="mx-2 text-slate-400">·</span>
                {dashboard.data.streak_days} day streak
              </>
            ) : (
              "Studio"
            )}
          </p>
          <div className="flex items-center gap-2">
            {clerkEnabled ? <UserButton /> : null}
            {devAuth && !clerkEnabled ? (
              <label className="text-sm">
                <span className="sr-only">Local session</span>
                <select
                  className="rounded-full border border-slate-300 bg-white px-3 py-2 dark:border-slate-600 dark:bg-slate-900"
                  value={devUserId}
                  onChange={(event) => setDevUserId(event.target.value)}
                >
                  <option value="demo-student">Demo student</option>
                  <option value="demo-instructor">Demo instructor</option>
                  <option value="demo-admin">Demo admin</option>
                </select>
              </label>
            ) : null}
            <ThemeToggle />
          </div>
        </header>
        <main id="main" className="px-5 py-6">
          {children}
        </main>
      </div>
    </div>
  );
}
