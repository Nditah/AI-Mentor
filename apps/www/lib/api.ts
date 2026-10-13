import { apiBase } from "@/lib/urls";

export type CatalogStats = {
  published: number;
  questions: number;
  challenges: number;
  paths: number;
  concepts: number;
  by_type: Record<string, number>;
  pack_paths: {
    slug: string;
    title: string;
    description: string;
    difficulty: string;
    estimated_minutes: number | null;
  }[];
  note: string;
};

export type CurriculumPath = {
  slug: string;
  title: string;
  description: string;
  level: string;
  concepts: number;
};

export type LeaderboardRow = {
  rank: number;
  display_name: string;
  xp: number;
  level: number;
  streak_days: number;
};

async function getJson<T>(path: string): Promise<T | null> {
  try {
    const response = await fetch(`${apiBase}${path}`, { next: { revalidate: 300 } });
    if (!response.ok) return null;
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

export function catalogStats(): Promise<CatalogStats | null> {
  return getJson<CatalogStats>("/api/v1/catalog/stats");
}

export function curriculumPaths(): Promise<CurriculumPath[] | null> {
  return getJson<CurriculumPath[]>("/api/v1/learning-paths");
}

export function publicLeaderboard(): Promise<LeaderboardRow[] | null> {
  return getJson<LeaderboardRow[]>("/api/v1/leaderboard");
}

export type LeadPayload = {
  kind: "instructor" | "enterprise" | "sales" | "support" | "partnership" | "content";
  name: string;
  email: string;
  organisation?: string;
  role?: string;
  seats?: number;
  country?: string;
  cohort_size?: number;
  start_month?: string;
  sso?: boolean;
  lms?: "canvas" | "moodle" | "other" | "none";
  message?: string;
  website?: string;
};

export async function submitLead(body: LeadPayload): Promise<{ ok: boolean; message: string }> {
  try {
    const response = await fetch(`${apiBase}/api/v1/leads`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (response.status === 202) {
      return { ok: true, message: "We will write within two working days. This form does not grant an app role." };
    }
    if (response.status === 422) {
      return { ok: false, message: "Check the required fields and try again." };
    }
    return { ok: false, message: "The form could not be sent. Try again shortly." };
  } catch {
    return { ok: false, message: "The form could not reach the server. Try again shortly." };
  }
}
