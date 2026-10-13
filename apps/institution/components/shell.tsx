"use client";

import { UserButton } from "@clerk/nextjs";
import {
  BookOpen,
  Calendar,
  ClipboardList,
  Database,
  GitBranch,
  LayoutDashboard,
  Library,
  ScrollText,
  Settings,
  Shield,
  Sparkles,
  Upload,
  Users,
  Waypoints,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { FormEvent, useEffect, useState } from "react";
import { api, devAuth, devUser, setDevUser, studioUrl } from "@/lib/api";
import { clerkEnabled } from "@/lib/csp";

const links = [
  ["/", "Overview", LayoutDashboard, "instructor"],
  ["/library", "Library", Library, "instructor"],
  ["/catalog", "Resource catalog", Database, "instructor"],
  ["/catalog/import", "Asset import", Upload, "instructor"],
  ["/catalog/quality", "Quality scores", ClipboardList, "instructor"],
  ["/catalog/duplicates", "Duplicates", ScrollText, "instructor"],
  ["/review", "Review queue", ClipboardList, "instructor"],
  ["/generate", "Generate", Sparkles, "instructor"],
  ["/curriculum", "Curriculum", BookOpen, "instructor"],
  ["/studio/paths", "Learning paths", BookOpen, "instructor"],
  ["/studio/assessments", "Assessments", ClipboardList, "instructor"],
  ["/studio/metadata", "Metadata", Settings, "instructor"],
  ["/taxonomy", "Taxonomy", GitBranch, "instructor"],
  ["/graph", "Knowledge graph", Waypoints, "instructor"],
  ["/challenges", "Challenges", Calendar, "instructor"],
  ["/analytics", "Analytics", LayoutDashboard, "instructor"],
  ["/moderation", "Moderation", Shield, "instructor"],
  ["/users", "Users", Users, "admin"],
  ["/configuration", "Configuration", Settings, "admin"],
  ["/providers", "AI providers", Sparkles, "admin"],
  ["/audit", "Audit log", ScrollText, "admin"],
] as const;

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
  const visible = links.filter((item) => role === "admin" || item[3] === "instructor");

  function onSession(event: FormEvent<HTMLSelectElement>) {
    setDevUser(event.currentTarget.value);
    window.location.reload();
  }

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[264px_1fr]">
      <aside className="border-b border-slate-200 bg-white px-4 py-4 dark:border-slate-800 dark:bg-slate-950 lg:border-b-0 lg:border-r">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">AI Mentor</p>
        <p className="text-lg font-semibold">Admin</p>
        <a className="mt-2 inline-block text-sm text-[#1d4ed8] underline" href={studioUrl}>
          Back to studio
        </a>
        <nav className="mt-4 flex gap-1 overflow-x-auto lg:flex-col" aria-label="Admin">
          {me.isPending ? <p className="px-3 py-2 text-sm text-slate-500">Loading navigation…</p> : null}
          {!me.isPending && visible.map(([href, label, Icon]) => {
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
        </nav>
      </aside>
      <div>
        <header className="flex items-center justify-between gap-3 border-b border-slate-200 px-5 py-3 dark:border-slate-800">
          <p className="text-sm">
            {me.data ? `${me.data.display_name} · ${me.data.role}` : "Admin portal"}
          </p>
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
          {role === "student" && me.data ? (
            <p className="max-w-xl">
              This portal is for instructors and admins.{" "}
              {clerkEnabled ? "Ask an admin to change your role." : "Switch the local session, or ask an admin to change your role."}
            </p>
          ) : (
            children
          )}
        </main>
      </div>
    </div>
  );
}
