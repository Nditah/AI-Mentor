"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import type { Dashboard } from "@/lib/types";
import { useStudio } from "@/stores/studio";

export default function DashboardPage() {
  const devUserId = useStudio((state) => state.devUserId);
  const query = useQuery({
    queryKey: ["dashboard", devUserId],
    queryFn: () => api<Dashboard>("/api/v1/dashboard"),
  });
  const carryOn = useQuery({
    queryKey: ["continue", devUserId],
    queryFn: () => api<{ continue: { href: string; lesson_title: string; title: string } | null }>("/api/v1/learn/continue"),
  });

  if (query.isLoading) return <p>Loading your dashboard…</p>;
  if (query.error) {
    const message = query.error instanceof ApiError ? query.error.message : "The mentor service is offline.";
    return (
      <section className="max-w-xl rounded-3xl border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900">
        <h1 className="font-display text-3xl">The Learner App cannot reach the mentor.</h1>
        <p className="mt-2 text-slate-700 dark:text-slate-300">{message}</p>
        <button className="mt-4 underline" type="button" onClick={() => query.refetch()}>
          Try again
        </button>
      </section>
    );
  }
  const data = query.data!;
  const width = Math.round((data.xp_into_level / data.xp_per_level) * 100);
  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-display text-4xl tracking-tight">Hello, {data.display_name}</h1>
        <p className="mt-1 text-slate-600 dark:text-slate-300">
          {data.lessons_completed} lessons completed · {data.quizzes_taken} quizzes · mastery {data.mastery}
        </p>
      </header>
      <section className="rounded-3xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900" aria-label="Experience">
        <div className="flex justify-between text-sm font-semibold">
          <span>Level {data.level}</span>
          <span>
            {data.xp_into_level} / {data.xp_per_level} XP
          </span>
        </div>
        <div className="mt-2 h-3 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800" role="meter" aria-valuenow={data.xp_into_level} aria-valuemin={0} aria-valuemax={data.xp_per_level} aria-label="Experience toward the next level">
          <div className="h-full rounded-full bg-[#10B981]" style={{ width: `${width}%` }} />
        </div>
      </section>
      {carryOn.data?.continue ? (
        <section className="rounded-3xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900">
          <h2 className="text-xl font-semibold">Continue where you left off</h2>
          <p className="mt-2 text-slate-700 dark:text-slate-300">
            {carryOn.data.continue.lesson_title} · {carryOn.data.continue.title}
          </p>
          <Link className="mt-3 inline-block font-semibold text-[#1d4ed8] underline" href={carryOn.data.continue.href}>
            Resume
          </Link>
        </section>
      ) : null}
      <section className="grid gap-4 lg:grid-cols-3">
        <ScoreList title="Strengths" items={data.strengths} empty="Nothing is strong yet. Finish a lesson and a quiz." />
        <ScoreList title="Developing" items={data.developing} empty="In-between scores show up here." />
        <ScoreList title="Gaps" items={data.weaknesses} empty="Gaps appear after an attempt, not before you start." />
      </section>
      <section className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <article className="rounded-3xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900">
          <h2 className="text-xl font-semibold">Recommended next</h2>
          <ul className="mt-3 space-y-3">
            {data.recommendations.map((item) => (
              <li key={item.slug}>
                <Link className="font-semibold text-[#1d4ed8] underline" href={`/paths`}>
                  {item.name}
                </Link>
                <p className="text-sm text-slate-600 dark:text-slate-300">{item.reason}</p>
              </li>
            ))}
          </ul>
        </article>
        <article className="rounded-3xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900">
          <h2 className="text-xl font-semibold">Paths</h2>
          <ul className="mt-3 space-y-3">
            {data.paths.map((path) => (
              <li key={path.slug}>
                <Link className="font-semibold underline" href={`/paths/${path.slug}`}>
                  {path.title}
                </Link>
                <p className="text-sm text-slate-600 dark:text-slate-300">
                  {path.completed} of {path.total}
                </p>
              </li>
            ))}
          </ul>
        </article>
      </section>
      <section aria-label="Badges">
        <h2 className="text-xl font-semibold">Badges</h2>
        <ul className="mt-3 flex flex-wrap gap-2">
          {data.badges.map((badge) => (
            <li
              key={badge.slug}
              className={
                badge.earned
                  ? "rounded-full bg-emerald-100 px-3 py-1 text-sm font-semibold text-emerald-950"
                  : "rounded-full border border-dashed border-slate-300 px-3 py-1 text-sm text-slate-500"
              }
            >
              {badge.name}
              <span className="sr-only">{badge.earned ? ", earned" : ", not earned"}</span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

function ScoreList({ title, items, empty }: { title: string; items: { slug: string; name: string; score: number }[]; empty: string }) {
  return (
    <article className="rounded-3xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900">
      <h2 className="text-lg font-semibold">{title}</h2>
      {items.length === 0 ? (
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{empty}</p>
      ) : (
        <ul className="mt-2 space-y-1 text-sm">
          {items.map((item) => (
            <li key={item.slug} className="flex justify-between">
              <span>{item.name}</span>
              <span>{item.score}</span>
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}
