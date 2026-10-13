"use client";

import { UserButton } from "@clerk/nextjs";
import {
  BarChart3,
  BookOpen,
  Building2,
  Calendar,
  ClipboardList,
  CreditCard,
  LayoutDashboard,
  MessageSquare,
  Settings,
  Shield,
  Users,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { FormEvent, useEffect, useState } from "react";
import { AppLauncher } from "@/components/app-launcher";
import { api, devAuth, devUser, setDevUser } from "@/lib/api";
import { clerkEnabled } from "@/lib/csp";

const sections: [string, [string, string, typeof LayoutDashboard][]][] = [
  ["Overview", [["/", "Overview", LayoutDashboard]]],
  ["Organisation", [["/organisation", "Structure", Building2], ["/organisation/cohorts", "Cohorts", Users], ["/organisation/terms", "Terms", Calendar]]],
  ["People", [["/people", "Members", Users], ["/people/instructors", "Instructors", Users], ["/people/admins", "Admins", Shield], ["/people/invitations", "Invitations", ClipboardList], ["/people/import", "Import", ClipboardList]]],
  ["Reports", [["/reports", "Library", BarChart3], ["/reports/schedules", "Schedules", Calendar], ["/reports/workforce", "Workforce", BarChart3]]],
  ["Licences and billing", [["/licences", "Licences", CreditCard], ["/licences/seats", "Seats", Users], ["/licences/invoices", "Invoices", ClipboardList]]],
  ["Compliance", [["/compliance", "Overview", Shield], ["/compliance/data-requests", "Data requests", ClipboardList], ["/compliance/retention", "Retention", ClipboardList], ["/compliance/consent", "Consent", ClipboardList], ["/compliance/audit", "Audit log", ClipboardList]]],
  ["Settings", [["/settings/profile", "Profile", Settings], ["/settings/branding", "Branding", Settings], ["/settings/content", "Content", BookOpen]]],
];

type Me = { display_name: string; role: string };

export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  const orgMatch = pathname.match(/^\/o\/([^/]+)/);
  const org = orgMatch?.[1] || "demo";
  const prefix = `/o/${org}`;

  const [session, setSession] = useState("demo-instructor");
  useEffect(() => setSession(devUser()), []);
  const me = useQuery({
    queryKey: ["me", session],
    queryFn: () => api<Me>("/api/v1/me"),
  });
  const role = me.data?.role || "student";

  function onSession(event: FormEvent<HTMLSelectElement>) {
    setDevUser(event.currentTarget.value);
    window.location.reload();
  }

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[264px_1fr]">
      <aside className="border-b border-slate-200 bg-white px-4 py-4 dark:border-slate-800 dark:bg-slate-950 lg:border-b-0 lg:border-r">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">AI Mentor</p>
        <p className="text-lg font-semibold">Institution</p>
        <AppLauncher current="institution" />
        <nav className="mt-4 flex gap-1 overflow-x-auto lg:flex-col" aria-label="Institution">
          {me.isPending ? <p className="px-3 py-2 text-sm text-slate-500">Loading navigation…</p> : null}
          {!me.isPending &&
            sections.map(([heading, links]) => (
              <div key={heading} className="mt-3">
                <p className="px-3 text-xs font-semibold uppercase tracking-wide text-slate-500">{heading}</p>
                {links.map(([href, label, Icon]) => {
                  const full = prefix + href;
                  const active = href === "/" ? pathname === prefix || pathname === `${prefix}/` : pathname === full || pathname.startsWith(`${full}/`);
                  return (
                    <Link
                      key={href}
                      href={full}
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
          <p className="text-sm">{me.data ? `${me.data.display_name} · ${me.data.role}` : "Institution"}</p>
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
            <p className="max-w-xl">This app is for institution administrators. Open the Instructor App or Learner App from the launcher.</p>
          ) : (
            children
          )}
        </main>
      </div>
    </div>
  );
}
