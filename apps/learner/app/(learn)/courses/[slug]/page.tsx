"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { use } from "react";
import { api } from "@/lib/api";
import { useStudio } from "@/stores/studio";

type ModuleCard = { slug: string; title: string; summary: string; progress: number };
type Assessment = { id: string; title: string; pass_score: number; passed: boolean };

export default function CoursePage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = use(params);
  const devUserId = useStudio((state) => state.devUserId);
  const query = useQuery({
    queryKey: ["course", slug, devUserId],
    queryFn: () =>
      api<{
        title: string;
        description: string;
        progress: number;
        pass_score: number;
        path: { slug: string; title: string } | null;
        modules: ModuleCard[];
        assessment: Assessment | null;
      }>(`/api/v1/learn/courses/${slug}`),
  });
  if (query.isLoading) return <p>Loading the course…</p>;
  if (!query.data) return <p>That course was not found.</p>;
  const course = query.data;
  return (
    <div>
      <p className="text-sm">
        {course.path ? <Link className="underline" href={`/paths/${course.path.slug}`}>{course.path.title}</Link> : null}
      </p>
      <h1 className="mt-2 font-display text-4xl tracking-tight">{course.title}</h1>
      <p className="mt-2 max-w-3xl text-slate-700 dark:text-slate-300">{course.description}</p>
      <p className="mt-2 text-sm font-semibold">{course.progress}% · course assessment pass mark {course.pass_score}%</p>
      <ol className="mt-6 space-y-4">
        {course.modules.map((module) => (
          <li key={module.slug} className="rounded-3xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900">
            <p className="text-sm font-semibold text-[#1d4ed8]">{module.progress}%</p>
            <h2 className="text-2xl font-semibold">
              <Link className="underline" href={`/modules/${module.slug}`}>{module.title}</Link>
            </h2>
            <p className="mt-2 text-slate-700 dark:text-slate-300">{module.summary}</p>
          </li>
        ))}
      </ol>
      {course.assessment ? (
        <p className="mt-6">
          <Link className="font-semibold underline" href={`/assessments/${course.assessment.id}`}>
            {course.assessment.title}{course.assessment.passed ? " · passed" : ""}
          </Link>
        </p>
      ) : null}
    </div>
  );
}
