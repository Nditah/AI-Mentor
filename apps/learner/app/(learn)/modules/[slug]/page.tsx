"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { use } from "react";
import { api } from "@/lib/api";
import { useStudio } from "@/stores/studio";

type LessonCard = {
  slug: string;
  title: string;
  summary: string;
  estimated_minutes: number;
  progress: number;
  href: string | null;
};
type Assessment = { id: string; title: string; pass_score: number; passed: boolean };

export default function ModulePage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = use(params);
  const devUserId = useStudio((state) => state.devUserId);
  const query = useQuery({
    queryKey: ["module", slug, devUserId],
    queryFn: () =>
      api<{
        title: string;
        summary: string;
        progress: number;
        pass_score: number;
        course: { slug: string; title: string } | null;
        lessons: LessonCard[];
        assessment: Assessment | null;
      }>(`/api/v1/learn/modules/${slug}`),
  });
  if (query.isLoading) return <p>Loading the module…</p>;
  if (!query.data) return <p>That module was not found.</p>;
  const module = query.data;
  return (
    <div>
      <p className="text-sm">
        {module.course ? <Link className="underline" href={`/courses/${module.course.slug}`}>{module.course.title}</Link> : null}
      </p>
      <h1 className="mt-2 font-display text-4xl tracking-tight">{module.title}</h1>
      <p className="mt-2 max-w-3xl text-slate-700 dark:text-slate-300">{module.summary}</p>
      <p className="mt-2 text-sm font-semibold">{module.progress}% · module assessment pass mark {module.pass_score}%</p>
      <ol className="mt-6 space-y-3">
        {module.lessons.map((lesson) => (
          <li key={lesson.slug} className="rounded-3xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900">
            <p className="text-sm font-semibold text-[#1d4ed8]">{lesson.progress}% · {lesson.estimated_minutes} min</p>
            <h2 className="text-xl font-semibold">
              {lesson.href ? <Link className="underline" href={lesson.href}>{lesson.title}</Link> : lesson.title}
            </h2>
            <p className="mt-1 text-slate-700 dark:text-slate-300">{lesson.summary}</p>
          </li>
        ))}
      </ol>
      {module.assessment ? (
        <p className="mt-6">
          <Link className="font-semibold underline" href={`/assessments/${module.assessment.id}`}>
            {module.assessment.title}{module.assessment.passed ? " · passed" : ""}
          </Link>
        </p>
      ) : null}
    </div>
  );
}
