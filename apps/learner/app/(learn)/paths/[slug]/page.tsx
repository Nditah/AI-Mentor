"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { use } from "react";
import { ApiError, api } from "@/lib/api";
import { useStudio } from "@/stores/studio";

type CourseCard = { slug: string; title: string; description: string; progress: number };
type Assessment = { id: string; title: string; pass_score: number; passed: boolean; best_score: number | null };
type PathDetail = {
  title: string;
  description: string;
  level: string;
  progress: number;
  xp_reward: number;
  academy: { slug: string; title: string } | null;
  courses: CourseCard[];
  assessment: Assessment | null;
  next_path: { slug: string; title: string; locked: boolean } | null;
};

export default function PathDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = use(params);
  const devUserId = useStudio((state) => state.devUserId);
  const query = useQuery({
    queryKey: ["learn-path", slug, devUserId],
    queryFn: () => api<PathDetail>(`/api/v1/learn/paths/${slug}`),
  });
  if (query.isLoading) return <p>Loading the path…</p>;
  if (query.error) {
    const message = query.error instanceof ApiError ? query.error.message : "That path was not found.";
    return <p>{message}</p>;
  }
  if (!query.data) return <p>That path was not found.</p>;
  const path = query.data;
  return (
    <div>
      <p className="text-sm">
        <Link className="underline" href="/academies">World</Link>
        {path.academy ? (
          <>
            {" · "}
            <Link className="underline" href={`/academies/${path.academy.slug}`}>
              {path.academy.title}
            </Link>
          </>
        ) : null}
      </p>
      <p className="mt-2 text-sm font-semibold uppercase tracking-wide text-[#1d4ed8]">{path.level}</p>
      <h1 className="font-display text-4xl tracking-tight">{path.title}</h1>
      <p className="mt-2 max-w-3xl text-slate-700 dark:text-slate-300">{path.description}</p>
      <p className="mt-2 text-sm font-semibold">{path.progress}% of this path · {path.xp_reward} XP when you finish it</p>
      <ol className="mt-6 space-y-4">
        {path.courses.map((course) => (
          <li key={course.slug} className="rounded-3xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900">
            <p className="text-sm font-semibold text-[#1d4ed8]">{course.progress}% complete</p>
            <h2 className="text-2xl font-semibold">
              <Link className="underline" href={`/courses/${course.slug}`}>{course.title}</Link>
            </h2>
            <p className="mt-2 text-slate-700 dark:text-slate-300">{course.description}</p>
          </li>
        ))}
      </ol>
      {path.assessment ? (
        <p className="mt-6">
          <Link className="font-semibold underline" href={`/assessments/${path.assessment.id}`}>
            {path.assessment.title} · pass {path.assessment.pass_score}%{path.assessment.passed ? " · passed" : ""}
          </Link>
        </p>
      ) : null}
      {path.next_path ? (
        <p className="mt-4 text-sm">
          Next path: {path.next_path.locked ? `${path.next_path.title} unlocks at 100%` : <Link className="underline" href={`/paths/${path.next_path.slug}`}>{path.next_path.title}</Link>}
        </p>
      ) : null}
    </div>
  );
}
