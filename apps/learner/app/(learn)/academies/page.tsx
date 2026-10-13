"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { api } from "@/lib/api";
import { useStudio } from "@/stores/studio";

type AcademyCard = {
  slug: string;
  title: string;
  summary: string;
  paths: number;
  progress: number;
};

export default function AcademiesPage() {
  const devUserId = useStudio((state) => state.devUserId);
  const query = useQuery({
    queryKey: ["academies", devUserId],
    queryFn: () => api<AcademyCard[]>("/api/v1/learn/academies"),
  });
  return (
    <div>
      <h1 className="font-display text-4xl tracking-tight">Academies</h1>
      <p className="mt-2 max-w-2xl text-slate-700 dark:text-slate-300">
        Pick an academy, then a learning path, a course, a module, and a lesson. Each lesson is a short sequence of pages.
      </p>
      {query.isLoading ? <p className="mt-6">Loading academies…</p> : null}
      {query.error ? <p className="mt-6">Academies are unavailable.</p> : null}
      <div className="mt-6 grid gap-4 md:grid-cols-2">
        {(query.data || []).map((academy) => (
          <article key={academy.slug} className="rounded-3xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900">
            <p className="text-sm font-semibold text-[#1d4ed8]">{academy.progress}% complete</p>
            <h2 className="mt-1 text-2xl font-semibold">
              <Link className="underline" href={`/academies/${academy.slug}`}>
                {academy.title}
              </Link>
            </h2>
            <p className="mt-2 text-slate-700 dark:text-slate-300">{academy.summary}</p>
            <p className="mt-3 text-sm">{academy.paths} learning paths</p>
          </article>
        ))}
      </div>
    </div>
  );
}
