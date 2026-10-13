"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { api } from "@/lib/api";

type PathCard = { slug: string; title: string; description: string; level: string; concepts: number };

export default function PathsPage() {
  const query = useQuery({
    queryKey: ["paths"],
    queryFn: () => api<PathCard[]>("/api/v1/learning-paths"),
  });
  return (
    <div>
      <h1 className="font-display text-4xl tracking-tight">Learning paths</h1>
      <p className="mt-2 max-w-2xl text-slate-700 dark:text-slate-300">
        Each step lists the concepts it depends on. Recommendations on the dashboard stay behind those dependencies.
      </p>
      {query.isLoading ? <p className="mt-6">Loading paths…</p> : null}
      {query.error ? <p className="mt-6">Paths are unavailable.</p> : null}
      <div className="mt-6 grid gap-4 md:grid-cols-2">
        {(query.data || []).map((path) => (
          <article key={path.slug} className="rounded-3xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900">
            <p className="text-xs font-semibold uppercase tracking-wide text-[#1d4ed8]">{path.level}</p>
            <h2 className="mt-1 text-2xl font-semibold">
              <Link className="underline" href={`/paths/${path.slug}`}>
                {path.title}
              </Link>
            </h2>
            <p className="mt-2 text-slate-700 dark:text-slate-300">{path.description}</p>
            <p className="mt-3 text-sm">{path.concepts} concepts</p>
          </article>
        ))}
      </div>
    </div>
  );
}
