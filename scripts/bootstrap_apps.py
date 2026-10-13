"""One-shot writer for the five Next.js apps. Safe to re-run."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APPS = ROOT / "apps"

LAUNCHER = '''"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export type AppLink = {
  code: string;
  name: string;
  url: string;
  available: boolean;
};

export function AppLauncher({ current }: { current: string }) {
  const apps = useQuery({
    queryKey: ["me-apps"],
    queryFn: () => api<AppLink[]>("/api/v1/me/apps"),
  });
  const items = (apps.data || []).filter((item) => item.available && item.code !== current);
  if (!items.length) return null;
  return (
    <nav aria-label="Applications" className="mt-3 flex flex-col gap-1 text-sm">
      {items.map((item) => (
        <a key={item.code} className="rounded-full px-3 py-1 text-[#1d4ed8] underline" href={item.url}>
          {item.name}
        </a>
      ))}
    </nav>
  );
}
'''

QUEUE = '''"use client";

export function QueuePage({
  title,
  description,
  empty,
}: {
  title: string;
  description: string;
  empty: string;
}) {
  return (
    <div>
      <h1 className="text-3xl font-semibold tracking-tight">{title}</h1>
      <p className="mt-2 max-w-2xl text-slate-600 dark:text-slate-300">{description}</p>
      <p className="mt-8 rounded-2xl border border-dashed border-slate-300 bg-white p-6 text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300">
        {empty}
      </p>
    </div>
  );
}
'''

API_TS = '''import { sessionToken } from "@/lib/auth";

export const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export const devAuth = process.env.NEXT_PUBLIC_DEV_AUTH === "true";

const key = "ai-mentor-{app}-user";
const fallback = "{dev_user}";

export function devUser(): string {
  if (typeof window === "undefined") return fallback;
  return window.localStorage.getItem(key) || fallback;
}

export function setDevUser(id: string) {
  window.localStorage.setItem(key, id);
}

export class ApiError extends Error {
  status: number;
  traceId?: string;
  constructor(status: number, message: string, traceId?: string) {
    super(message);
    this.status = traceId;
    this.traceId = traceId;
  }
}

type Problem = { detail?: string; trace_id?: string; errors?: { path: string; message: string }[] };

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token = await sessionToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  else if (devAuth) headers.set("X-Dev-User-Id", devUser());
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(`${apiBase}${path}`, { ...init, headers });
  if (!response.ok) {
    let detail = response.statusText;
    let traceId: string | undefined;
    try {
      const problem = (await response.json()) as Problem;
      if (problem.detail) detail = problem.detail;
      if (problem.errors?.length) detail = problem.errors.map((item) => item.message).join(" ");
      traceId = problem.trace_id;
    } catch {
      detail = response.statusText;
    }
    throw new ApiError(response.status, detail, traceId);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}
'''

# Fix the accidental constructor bug above when writing
API_TS = API_TS.replace(
    "this.status = traceId;\n    this.traceId = traceId;",
    "this.status = status;\n    this.traceId = traceId;",
)

ENV = """NEXT_PUBLIC_API_URL=http://localhost:8000
# Shows the local session switcher. A production build refuses this.
NEXT_PUBLIC_DEV_AUTH=true
NEXT_PUBLIC_LEARNER_URL=http://localhost:3000
NEXT_PUBLIC_ADMIN_URL=http://localhost:3001
NEXT_PUBLIC_INSTRUCTOR_URL=http://localhost:3002
NEXT_PUBLIC_INSTITUTION_URL=http://localhost:3003
NEXT_PUBLIC_STUDIO_URL=http://localhost:3004
# Set to sign in with Clerk. Required for a production build.
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=
CLERK_SECRET_KEY=
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
# Send the CSP as Report-Only (first week of a new policy), then remove.
CSP_REPORT_ONLY=
"""

PACKAGE = """{
  "name": "ai-mentor-{name}",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev --port {port}",
    "build": "next build",
    "start": "next start --port {port}",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "@clerk/nextjs": "^6.39.7",
    "@tanstack/react-query": "^5.67.2",
    "lucide-react": "^0.487.0",
    "next": "^16.4.0",
    "react": "^19.1.0",
    "react-dom": "^19.1.0"
  },
  "devDependencies": {
    "@types/node": "^22.14.0",
    "@types/react": "^19.1.0",
    "@types/react-dom": "^19.1.0",
    "autoprefixer": "^10.4.21",
    "postcss": "^8.5.3",
    "tailwindcss": "^3.4.17",
    "typescript": "^5.8.3"
  }
}
"""

SHELL_HEAD = '''"use client";

import { UserButton } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { AppLauncher } from "@/components/app-launcher";
import { api, devAuth, devUser, setDevUser } from "@/lib/api";
import { clerkEnabled } from "@/lib/csp";
import type { LucideIcon } from "lucide-react";
{icons}

type Me = { display_name: string; role: string };
type LinkItem = [string, string, LucideIcon];

'''

ADMIN_SHELL = r'''"use client";

import { UserButton } from "@clerk/nextjs";
import {
  Building2,
  ClipboardList,
  LayoutDashboard,
  ScrollText,
  Settings,
  Shield,
  Sparkles,
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
  ["Operations", [["/", "Home", LayoutDashboard]]],
  ["Organisations and users", [["/users", "Users", Users], ["/organisations", "Organisations", Building2]]],
  ["AI services", [["/providers", "Providers", Sparkles]]],
  ["Platform", [["/configuration", "Settings", Settings]]],
  ["Trust and governance", [["/moderation", "Moderation", Shield], ["/audit", "Audit log", ScrollText]]],
  ["Insights", [["/analytics", "Analytics", ClipboardList]]],
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

  function onSession(event: FormEvent<HTMLSelectElement>) {
    setDevUser(event.currentTarget.value);
    window.location.reload();
  }

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[264px_1fr]">
      <aside className="border-b border-slate-200 bg-white px-4 py-4 dark:border-slate-800 dark:bg-slate-950 lg:border-b-0 lg:border-r">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">AI Mentor</p>
        <p className="text-lg font-semibold">Admin</p>
        <AppLauncher current="admin" />
        <nav className="mt-4 flex gap-1 overflow-x-auto lg:flex-col" aria-label="Admin">
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
          <p className="text-sm">{me.data ? `${me.data.display_name} · ${me.data.role}` : "Admin App"}</p>
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
          {role !== "admin" && me.data ? (
            <p className="max-w-xl">
              This app is for platform operators. Open Content Studio or the Instructor App from the launcher,
              or ask an admin to grant the admin role.
            </p>
          ) : (
            children
          )}
        </main>
      </div>
    </div>
  );
}
'''

STUDIO_SHELL = r'''"use client";

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
'''


def staff_shell(code: str, title: str, min_role: str, sections_ts: str, org_prefix: bool) -> str:
    prefix = (
        """
  const orgMatch = pathname.match(/^\\/o\\/([^/]+)/);
  const org = orgMatch?.[1] || "demo";
  const prefix = `/o/${org}`;
"""
        if org_prefix
        else "  const prefix = '';\n"
    )
    href_expr = "prefix + href" if org_prefix else "href"
    active_expr = (
        'href === "/" ? pathname === prefix || pathname === `${prefix}/` : '
        "pathname === full || pathname.startsWith(`${full}/`)"
        if org_prefix
        else 'href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`)'
    )
    gate = (
        'role !== "admin"'
        if min_role == "admin"
        else 'role === "student"'
    )
    refuse = (
        "This app is for institution administrators. Open the Instructor App or Learner App from the launcher."
        if code == "institution"
        else "This app is for instructors. Open the Learner App from the launcher, or ask an admin to change your role."
    )
    return f'''"use client";

import {{ UserButton }} from "@clerk/nextjs";
import {{
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
}} from "lucide-react";
import Link from "next/link";
import {{ usePathname }} from "next/navigation";
import {{ useQuery }} from "@tanstack/react-query";
import {{ FormEvent, useEffect, useState }} from "react";
import {{ AppLauncher }} from "@/components/app-launcher";
import {{ api, devAuth, devUser, setDevUser }} from "@/lib/api";
import {{ clerkEnabled }} from "@/lib/csp";

const sections: [string, [string, string, typeof LayoutDashboard][]][] = {sections_ts};

type Me = {{ display_name: string; role: string }};

export function Shell({{ children }}: {{ children: React.ReactNode }}) {{
  const pathname = usePathname();
{prefix}
  const [session, setSession] = useState("{('demo-instructor' if code != 'admin' else 'demo-admin')}");
  useEffect(() => setSession(devUser()), []);
  const me = useQuery({{
    queryKey: ["me", session],
    queryFn: () => api<Me>("/api/v1/me"),
  }});
  const role = me.data?.role || "student";

  function onSession(event: FormEvent<HTMLSelectElement>) {{
    setDevUser(event.currentTarget.value);
    window.location.reload();
  }}

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[264px_1fr]">
      <aside className="border-b border-slate-200 bg-white px-4 py-4 dark:border-slate-800 dark:bg-slate-950 lg:border-b-0 lg:border-r">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">AI Mentor</p>
        <p className="text-lg font-semibold">{title}</p>
        <AppLauncher current="{code}" />
        <nav className="mt-4 flex gap-1 overflow-x-auto lg:flex-col" aria-label="{title}">
          {{me.isPending ? <p className="px-3 py-2 text-sm text-slate-500">Loading navigation…</p> : null}}
          {{!me.isPending &&
            sections.map(([heading, links]) => (
              <div key={{heading}} className="mt-3">
                <p className="px-3 text-xs font-semibold uppercase tracking-wide text-slate-500">{{heading}}</p>
                {{links.map(([href, label, Icon]) => {{
                  const full = {href_expr};
                  const active = {active_expr};
                  return (
                    <Link
                      key={{href}}
                      href={{full}}
                      aria-current={{active ? "page" : undefined}}
                      className={{
                        active
                          ? "flex items-center gap-2 rounded-full bg-[#1d4ed8] px-3 py-2 text-sm font-semibold text-white"
                          : "flex items-center gap-2 rounded-full px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"
                      }}
                    >
                      <Icon aria-hidden size={{16}} />
                      {{label}}
                    </Link>
                  );
                }})}}
              </div>
            ))}}
        </nav>
      </aside>
      <div>
        <header className="flex items-center justify-between gap-3 border-b border-slate-200 px-5 py-3 dark:border-slate-800">
          <p className="text-sm">{{me.data ? `${{me.data.display_name}} · ${{me.data.role}}` : "{title}"}}</p>
          {{clerkEnabled ? <UserButton /> : null}}
          {{devAuth && !clerkEnabled ? (
            <label className="text-sm">
              <span className="sr-only">Local session</span>
              <select
                className="rounded-full border border-slate-300 bg-white px-3 py-2 dark:border-slate-600 dark:bg-slate-900"
                value={{session}}
                onChange={{onSession}}
              >
                <option value="demo-admin">Demo admin</option>
                <option value="demo-instructor">Demo instructor</option>
                <option value="demo-student">Demo student</option>
              </select>
            </label>
          ) : null}}
        </header>
        <main id="main" className="px-5 py-6">
          {{{gate} && me.data ? (
            <p className="max-w-xl">{refuse}</p>
          ) : (
            children
          )}}
        </main>
      </div>
    </div>
  );
}}
'''


INSTRUCTOR_SECTIONS = """[
  ["Home", [["/", "Home", LayoutDashboard], ["/calendar", "Calendar", Calendar]]],
  ["Cohorts", [["/cohorts", "Cohorts", Users]]],
  ["Learners", [["/learners", "Learners", Users], ["/learners/import", "Import", ClipboardList], ["/learners/invites", "Invites", ClipboardList]]],
  ["Assessments", [["/assessments", "Library", BookOpen], ["/assessments/rubrics", "Rubrics", ClipboardList]]],
  ["Marking", [["/marking", "Queue", ClipboardList], ["/marking/requests", "Review requests", ClipboardList]]],
  ["Messages", [["/messages", "Announcements", MessageSquare]]],
  ["Insights", [["/insights", "Insights", BarChart3]]],
]"""

INSTITUTION_SECTIONS = """[
  ["Overview", [["/", "Overview", LayoutDashboard]]],
  ["Organisation", [["/organisation", "Structure", Building2], ["/organisation/cohorts", "Cohorts", Users], ["/organisation/terms", "Terms", Calendar]]],
  ["People", [["/people", "Members", Users], ["/people/instructors", "Instructors", Users], ["/people/admins", "Admins", Shield], ["/people/invitations", "Invitations", ClipboardList], ["/people/import", "Import", ClipboardList]]],
  ["Reports", [["/reports", "Library", BarChart3], ["/reports/schedules", "Schedules", Calendar], ["/reports/workforce", "Workforce", BarChart3]]],
  ["Licences and billing", [["/licences", "Licences", CreditCard], ["/licences/seats", "Seats", Users], ["/licences/invoices", "Invoices", ClipboardList]]],
  ["Compliance", [["/compliance", "Overview", Shield], ["/compliance/data-requests", "Data requests", ClipboardList], ["/compliance/retention", "Retention", ClipboardList], ["/compliance/consent", "Consent", ClipboardList], ["/compliance/audit", "Audit log", ScrollText if false else ClipboardList]]],
  ["Settings", [["/settings/profile", "Profile", Settings], ["/settings/branding", "Branding", Settings], ["/settings/content", "Content", BookOpen]]],
]"""

# Fix the ScrollText hack - we imported ClipboardList not ScrollText. Use Shield/ClipboardList.


INSTITUTION_SECTIONS = """[
  ["Overview", [["/", "Overview", LayoutDashboard]]],
  ["Organisation", [["/organisation", "Structure", Building2], ["/organisation/cohorts", "Cohorts", Users], ["/organisation/terms", "Terms", Calendar]]],
  ["People", [["/people", "Members", Users], ["/people/instructors", "Instructors", Users], ["/people/admins", "Admins", Shield], ["/people/invitations", "Invitations", ClipboardList], ["/people/import", "Import", ClipboardList]]],
  ["Reports", [["/reports", "Library", BarChart3], ["/reports/schedules", "Schedules", Calendar], ["/reports/workforce", "Workforce", BarChart3]]],
  ["Licences and billing", [["/licences", "Licences", CreditCard], ["/licences/seats", "Seats", Users], ["/licences/invoices", "Invoices", ClipboardList]]],
  ["Compliance", [["/compliance", "Overview", Shield], ["/compliance/data-requests", "Data requests", ClipboardList], ["/compliance/retention", "Retention", ClipboardList], ["/compliance/consent", "Consent", ClipboardList], ["/compliance/audit", "Audit log", ClipboardList]]],
  ["Settings", [["/settings/profile", "Profile", Settings], ["/settings/branding", "Branding", Settings], ["/settings/content", "Content", BookOpen]]],
]"""


INSTRUCTOR_PAGES = [
    ("calendar/page.tsx", "Calendar", "Plan items and live sessions across your cohorts.", "No sessions are scheduled. Pin a path release to a cohort to populate the calendar."),
    ("cohorts/page.tsx", "Cohorts", "Classes you teach in this organisation.", "No cohorts yet. Create a cohort to pin a learning-path release and invite learners."),
    ("cohorts/new/page.tsx", "New cohort", "Lead instructors create a cohort, pin a release, and invite staff.", "Cohort creation will call POST /api/v1/orgs/{org_id}/cohorts when tenancy lands. Until then this form is not submitted."),
    ("learners/page.tsx", "Learners", "People enrolled in your cohorts.", "No learners in this organisation yet. Import a roster or send invites."),
    ("learners/import/page.tsx", "Import learners", "Upload a roster for this organisation.", "Roster import is waiting on the organisation membership API. Files are not uploaded from this screen yet."),
    ("learners/invites/page.tsx", "Invites", "Pending enrolment codes and invite links.", "No pending invites."),
    ("assessments/page.tsx", "Assessments", "Organisation assessment library. Answer keys stay on the server.", "No assessments in this organisation. Create a quiz in Content Studio and assign it here."),
    ("assessments/rubrics/page.tsx", "Rubrics", "Shared marking criteria for written work.", "No rubrics yet."),
    ("marking/page.tsx", "Marking queue", "Submissions waiting across your cohorts.", "The marking queue is empty. Assignments appear here after learners submit."),
    ("marking/requests/page.tsx", "Grade review requests", "Learners asking for a mark to be looked at again.", "No review requests."),
    ("messages/page.tsx", "Messages", "Announcements and threads for your cohorts.", "No announcements yet."),
    ("insights/page.tsx", "Insights", "Cross-cohort progress, risk, and attendance.", "Insights use organisation analytics once tenancy is on. Platform-wide counts stay in the Admin App."),
]

INSTITUTION_PAGES = [
    ("organisation/page.tsx", "Organisation structure", "Campuses and departments (at most two levels).", "This organisation has no units yet. Add a campus or department to group cohorts."),
    ("organisation/cohorts/page.tsx", "Cohorts", "Every class in the organisation, at scale.", "No cohorts. Instructors create them in the Instructor App."),
    ("organisation/terms/page.tsx", "Terms", "Academic terms and roll-over.", "No terms defined."),
    ("people/page.tsx", "People", "Memberships in this organisation.", "No members yet. Invite instructors and learners, or import a roster."),
    ("people/instructors/page.tsx", "Instructors", "Staff with a teaching assignment.", "No instructors assigned."),
    ("people/admins/page.tsx", "Organisation admins", "Role assignments at organisation scope.", "You are using the v1 instructor/admin rank until scoped RBAC ships. Platform admins still live in the Admin App."),
    ("people/invitations/page.tsx", "Invitations", "Open invites to this organisation.", "No invitations pending."),
    ("people/import/page.tsx", "Import people", "Bulk membership import.", "Import is waiting on the organisation membership API."),
    ("reports/page.tsx", "Reports", "Saved report definitions for this organisation.", "No reports saved. Workforce and licence reports appear here after the first licence is issued."),
    ("reports/schedules/page.tsx", "Report schedules", "Email or export a report on a cadence.", "No schedules."),
    ("reports/workforce/page.tsx", "Workforce development", "Readiness against licensed paths.", "No workforce report yet."),
    ("licences/page.tsx", "Licences", "Seats this organisation has bought.", "No licences on file. Billing is Stripe Checkout on the Learner App until organisation invoices ship."),
    ("licences/seats/page.tsx", "Seats", "Who occupies a licensed seat.", "No seats assigned."),
    ("licences/invoices/page.tsx", "Invoices", "Organisation billing history.", "No invoices."),
    ("compliance/page.tsx", "Compliance", "Data requests, retention, consent, and the organisation audit log.", "Open a data request from the list when a learner or regulator asks."),
    ("compliance/data-requests/page.tsx", "Data requests", "DSARs for people in this organisation.", "No data requests."),
    ("compliance/retention/page.tsx", "Retention", "How long membership and grade records are kept.", "Default retention follows the platform policy until an organisation override exists."),
    ("compliance/consent/page.tsx", "Consent", "Leaderboard, research, and analytics consent.", "No consent records to review."),
    ("compliance/audit/page.tsx", "Organisation audit log", "Actions in this tenant.", "The platform audit log stays in the Admin App. This view lists organisation-scoped events once tenancy is on."),
    ("settings/profile/page.tsx", "Organisation profile", "Name, kind, locale, time zone, and labels.", "Profile edits will call PATCH /api/v1/orgs/{org_id}."),
    ("settings/branding/page.tsx", "Branding", "Logo, colours, and login background for this organisation.", "Branding is not stored yet. White-label domains arrive in R4."),
    ("settings/content/page.tsx", "Content", "Licensed catalogue and the organisation workspace in Content Studio.", "Open Content Studio to work in an organisation workspace. Instructors consume published releases; they do not own the master repository."),
]


HOME_INSTRUCTOR = '''"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";

type Overview = {
  users: number;
  students: number;
  published: number;
  review_queue: number;
  quizzes_taken: number;
  note: string;
};

export default function InstructorHome({ params }: { params: { orgSlug: string } }) {
  const query = useQuery({
    queryKey: ["overview", params.orgSlug],
    queryFn: () => api<Overview>("/api/v1/admin/overview"),
    retry: false,
  });
  if (query.error instanceof ApiError) return <p>{query.error.message}</p>;
  if (!query.data) return <p>Loading your teaching home…</p>;
  const data = query.data;
  const base = `/o/${params.orgSlug}`;
  return (
    <div>
      <h1 className="text-3xl font-semibold tracking-tight">Teaching home</h1>
      <p className="mt-2 max-w-2xl text-slate-600 dark:text-slate-300">
        Queues for {params.orgSlug}. Instructors consume published path releases; they do not edit the master
        catalog. That work lives in Content Studio.
      </p>
      <dl className="mt-6 grid gap-3 sm:grid-cols-3">
        {[
          ["Learners (platform)", data.students],
          ["Published resources", data.published],
          ["Quizzes taken", data.quizzes_taken],
        ].map(([label, value]) => (
          <div key={String(label)} className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
            <dt className="text-sm text-slate-600 dark:text-slate-300">{label}</dt>
            <dd className="text-3xl font-semibold">{value}</dd>
          </div>
        ))}
      </dl>
      <ul className="mt-8 space-y-2">
        <li><Link className="underline" href={`${base}/cohorts`}>Open cohorts</Link></li>
        <li><Link className="underline" href={`${base}/marking`}>Marking queue</Link></li>
        <li><Link className="underline" href={`${base}/learners`}>All learners</Link></li>
      </ul>
    </div>
  );
}
'''

HOME_INSTITUTION = '''"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";

type Overview = {
  users: number;
  students: number;
  published: number;
  note: string;
};

export default function InstitutionHome({ params }: { params: { orgSlug: string } }) {
  const query = useQuery({
    queryKey: ["overview", params.orgSlug],
    queryFn: () => api<Overview>("/api/v1/admin/overview"),
    retry: false,
  });
  if (query.error instanceof ApiError) return <p>{query.error.message}</p>;
  if (!query.data) return <p>Loading the organisation…</p>;
  const data = query.data;
  const base = `/o/${params.orgSlug}`;
  return (
    <div>
      <h1 className="text-3xl font-semibold tracking-tight">Organisation overview</h1>
      <p className="mt-2 max-w-2xl text-slate-600 dark:text-slate-300">
        {params.orgSlug} on the shared platform. Licences, people, and compliance live here. Teaching lives in
        the Instructor App. Master content lives in Content Studio.
      </p>
      <dl className="mt-6 grid gap-3 sm:grid-cols-3">
        {[
          ["People (platform)", data.users],
          ["Learners", data.students],
          ["Published resources", data.published],
        ].map(([label, value]) => (
          <div key={String(label)} className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
            <dt className="text-sm text-slate-600 dark:text-slate-300">{label}</dt>
            <dd className="text-3xl font-semibold">{value}</dd>
          </div>
        ))}
      </dl>
      <ul className="mt-8 space-y-2">
        <li><Link className="underline" href={`${base}/people`}>People</Link></li>
        <li><Link className="underline" href={`${base}/licences`}>Licences</Link></li>
        <li><Link className="underline" href={`${base}/compliance`}>Compliance</Link></li>
      </ul>
    </div>
  );
}
'''

REDIRECT_ROOT = '''import { redirect } from "next/navigation";

export default function RootPage() {
  redirect("/o/demo");
}
'''

ORG_LAYOUT = '''export default function OrgLayout({ children }: { children: React.ReactNode }) {
  return children;
}
'''

QUEUE_PAGE = '''"use client";

import { QueuePage } from "@/components/queue-page";

export default function Page() {
  return (
    <QueuePage
      title={TITLE}
      description={DESC}
      empty={EMPTY}
    />
  );
}
'''

ADMIN_ORGS = '''"use client";

import { QueuePage } from "@/components/queue-page";

export default function OrganisationsPage() {
  return (
    <QueuePage
      title="Organisations"
      description="Every tenant on the platform. Membership, licences, and SSO status will list here."
      empty="Tenancy is not in the v1 schema yet. Demo organisation slug is demo. Create tenants after the organisations table lands."
    />
  );
}
'''

INSIGHTS_ANALYTICS = None  # instructor insights is a queue page; admin keeps analytics page


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content if content.endswith("\n") else content + "\n")


def write_queue(app: str, rel: str, title: str, desc: str, empty: str) -> None:
    body = (
        QUEUE_PAGE.replace("{TITLE}", json_str(title))
        .replace("{DESC}", json_str(desc))
        .replace("{EMPTY}", json_str(empty))
        .replace("title={TITLE}", f"title={json_str(title)}")
        .replace("description={DESC}", f"description={json_str(desc)}")
        .replace("empty={EMPTY}", f"empty={json_str(empty)}")
    )
    write(APPS / app / "app" / "o" / "[orgSlug]" / rel, body)


def json_str(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def patch_layout(app: str, title: str, description: str) -> None:
    path = APPS / app / "app" / "layout.tsx"
    text = path.read_text()
    text = text.replace(
        'title: { default: "Admin", template: "%s · AI Mentor Admin" }',
        f'title: {{ default: "{title}", template: "%s · AI Mentor {title}" }}',
    )
    text = text.replace(
        "Curate the knowledge library, review drafts, and manage the studio.",
        description,
    )
    path.write_text(text)


def main() -> None:
    for app, port, name, dev_user in [
        ("admin", 3001, "admin", "demo-admin"),
        ("instructor", 3002, "instructor", "demo-instructor"),
        ("institution", 3003, "institution", "demo-instructor"),
        ("studio", 3004, "studio", "demo-admin"),
    ]:
        root = APPS / app
        write(root / "components" / "app-launcher.tsx", LAUNCHER)
        write(root / "components" / "queue-page.tsx", QUEUE)
        write(root / ".env.example", ENV)
        write(root / "package.json", PACKAGE.format(name=name, port=port))
        api = API_TS.replace("{app}", app).replace("{dev_user}", dev_user)
        write(root / "lib" / "api.ts", api)

    write(APPS / "admin" / "components" / "shell.tsx", ADMIN_SHELL)
    write(APPS / "studio" / "components" / "shell.tsx", STUDIO_SHELL)
    write(
        APPS / "instructor" / "components" / "shell.tsx",
        staff_shell("instructor", "Instructor", "instructor", INSTRUCTOR_SECTIONS, True),
    )
    write(
        APPS / "institution" / "components" / "shell.tsx",
        staff_shell("institution", "Institution", "instructor", INSTITUTION_SECTIONS, True),
    )

    patch_layout("studio", "Content Studio", "Author, review, and publish the master knowledge repository.")
    patch_layout("instructor", "Instructor", "Teach cohorts, mark work, and intervene.")
    patch_layout("institution", "Institution", "Run the organisation: people, licences, compliance, and reports.")
    patch_layout("admin", "Admin", "Operate the platform: users, providers, trust, and analytics.")

    write(APPS / "admin" / "app" / "organisations" / "page.tsx", ADMIN_ORGS)

    write(APPS / "instructor" / "app" / "page.tsx", REDIRECT_ROOT)
    write(APPS / "institution" / "app" / "page.tsx", REDIRECT_ROOT)
    write(APPS / "instructor" / "app" / "o" / "[orgSlug]" / "layout.tsx", ORG_LAYOUT)
    write(APPS / "institution" / "app" / "o" / "[orgSlug]" / "layout.tsx", ORG_LAYOUT)
    write(APPS / "instructor" / "app" / "o" / "[orgSlug]" / "page.tsx", HOME_INSTRUCTOR)
    write(APPS / "institution" / "app" / "o" / "[orgSlug]" / "page.tsx", HOME_INSTITUTION)

    for rel, title, desc, empty in INSTRUCTOR_PAGES:
        write_queue("instructor", rel, title, desc, empty)
    for rel, title, desc, empty in INSTITUTION_PAGES:
        write_queue("institution", rel, title, desc, empty)

    # Studio home uses existing overview minus admin-only links
    write(
        APPS / "studio" / "app" / "page.tsx",
        (APPS / "admin" / "app" / "page.tsx").read_text()
        .replace("Overview", "Content Studio")
        .replace('href="/review"', 'href="/review"')
        .replace("Needs attention", "Needs attention"),
    )


if __name__ == "__main__":
    main()
