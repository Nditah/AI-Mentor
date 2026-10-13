"use client";

import { UserButton } from "@clerk/nextjs";
import {
  BookOpen,
  ClipboardList,
  Database,
  GitBranch,
  LayoutDashboard,
  Library,
  ScrollText,
  Settings,
  Sparkles,
  Upload,
  Waypoints,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { FormEvent, useEffect, useState } from "react";
import { AppLauncher } from "@/components/app-launcher";
import { api, devAuth, devUser, setDevUser } from "@/lib/api";
import { clerkEnabled } from "@/lib/csp";

const sections: [string, [string, string, typeof LayoutDashboard][]][] = [
  ["Home", [["/", "Overview", LayoutDashboard]]],
  [
    "Library",
    [
      ["/library", "Assets", Library],
      ["/catalog", "Resource catalog", Database],
      ["/catalog/import", "Import", Upload],
      ["/catalog/quality", "Quality", ClipboardList],
      ["/catalog/duplicates", "Duplicates", ScrollText],
    ],
  ],
  [
    "Build",
    [
      ["/curriculum", "Curricula", BookOpen],
      ["/studio/journey", "Journey", BookOpen],
      ["/studio/paths", "Paths", BookOpen],
      ["/studio/assessments", "Assessments", ClipboardList],
      ["/generate", "Generate", Sparkles],
      ["/challenges", "Challenges", ClipboardList],
    ],
  ],
  [
    "Knowledge",
    [
      ["/taxonomy", "Taxonomy", GitBranch],
      ["/graph", "Graph", Waypoints],
      ["/studio/metadata", "Metadata", Settings],
    ],
  ],
  ["Review", [["/review", "Review queue", ClipboardList]]],
];

type Me = { display_name: string; role: string };

export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [session, setSession] = useState("demo-admin");
  useEffect(() => setSession(devUser()), []);
  const me = useQuery({
    queryKey: ["me", session],
    queryFn: () => api<Me>("/api/v1/me"),
  });
  const role = me.data?.role || "student";
  const staff = role === "admin" || role === "instructor";

  function onSession(event: FormEvent<HTMLSelectElement>) {
    setDevUser(event.currentTarget.value);
    window.location.reload();
  }

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[264px_1fr]">
      <aside className="border-b border-slate-200 bg-white px-4 py-4 dark:border-slate-800 dark:bg-slate-950 lg:border-b-0 lg:border-r">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">AI Mentor</p>
        <p className="text-lg font-semibold">Content Studio</p>
        <AppLauncher current="studio" />
        <nav className="mt-4 flex gap-1 overflow-x-auto lg:flex-col" aria-label="Content Studio">
          {me.isPending ? <p className="px-3 py-2 text-sm text-slate-500">Loading navigation…</p> : null}
          {!me.isPending &&
            sections.map(([heading, links]) => (
              <div key={heading} className="mt-3">
                <p className="px-3 text-xs font-semibold uppercase tracking-wide text-slate-500">{heading}</p>
                {links.map(([href, label, Icon]) => {
                  const active = href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`);
                  return (
                    <Link
                      key={href}
                      href={href}
                      aria-current={active ? "page" : undefined}
                      className={
                        active
                          ? "flex items-center gap-2 rounded-full bg-[#1d4ed8] px-3 py-2 text-sm font-semibold text-white"
                          : "flex items-center gap-2 rounded-full px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"
                      }
                    >
                      <Icon aria-hidden size={16} />
                      {label}
                    </Link>
                  );
                })}
              </div>
            ))}
        </nav>
      </aside>
      <div>
        <header className="flex items-center justify-between gap-3 border-b border-slate-200 px-5 py-3 dark:border-slate-800">
          <p className="text-sm">{me.data ? `${me.data.display_name} · ${me.data.role}` : "Content Studio"}</p>
          {clerkEnabled ? <UserButton /> : null}
          {devAuth && !clerkEnabled ? (
            <label className="text-sm">
              <span className="sr-only">Local session</span>
              <select
                className="rounded-full border border-slate-300 bg-white px-3 py-2 dark:border-slate-600 dark:bg-slate-900"
                value={session}
                onChange={onSession}
              >
                <option value="demo-admin">Demo admin</option>
                <option value="demo-instructor">Demo instructor</option>
                <option value="demo-student">Demo student</option>
              </select>
            </label>
          ) : null}
        </header>
        <main id="main" className="px-5 py-6">
          {!staff && me.data ? (
            <p className="max-w-xl">
              Content Studio is for authors, reviewers, and publishers. Ask an admin to grant an instructor or
              admin role, or open the Learner App from the launcher.
            </p>
          ) : (
            children
          )}
        </main>
      </div>
    </div>
  );
}
