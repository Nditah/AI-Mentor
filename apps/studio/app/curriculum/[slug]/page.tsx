"use client";

import { use } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";

type Step = {
  position: number;
  slug: string | null;
  title: string;
  estimated_minutes: number | null;
  completed: boolean;
  prerequisites: string[];
};

type Path = {
  slug: string;
  title: string;
  description: string;
  level: string;
  steps: Step[];
};

export default function CurriculumDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = use(params);
  const query = useQuery({
    queryKey: ["path", slug],
    queryFn: () => api<Path>(`/api/v1/learning-paths/${slug}`),
    retry: false,
  });
  if (query.error instanceof ApiError) return <p>{query.error.message}</p>;
  if (!query.data) return <p>Loading the path…</p>;
  const path = query.data;
  return (
    <article className="max-w-3xl">
      <p className="text-sm font-semibold uppercase tracking-wide text-[#1d4ed8]">{path.level}</p>
      <h1 className="mt-1 text-3xl font-semibold tracking-tight">{path.title}</h1>
      <p className="mt-2 text-slate-700 dark:text-slate-300">{path.description}</p>
      <ol className="mt-6 space-y-3">
        {path.steps.map((step) => (
          <li key={`${step.position}-${step.slug || step.title}`} className="rounded-2xl border border-slate-200 p-4 dark:border-slate-700">
            <p className="font-semibold">
              {step.position}. {step.title}
            </p>
            <p className="text-sm text-slate-600 dark:text-slate-300">
              {step.estimated_minutes ? `${step.estimated_minutes} min` : "Open"}
              {step.slug ? ` · ${step.slug}` : ""}
              {step.prerequisites.length ? ` · needs ${step.prerequisites.join(", ")}` : ""}
            </p>
          </li>
        ))}
      </ol>
      <p className="mt-8 text-sm">
        <Link className="underline" href="/curriculum">
          Back to curriculum
        </Link>
      </p>
    </article>
  );
}
