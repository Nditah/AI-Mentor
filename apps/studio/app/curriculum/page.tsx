"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { api } from "@/lib/api";

type PathCard = { slug: string; title: string; description: string; level: string; concepts: number };

export default function CurriculumPage() {
  const query = useQuery({
    queryKey: ["paths"],
    queryFn: () => api<PathCard[]>("/api/v1/learning-paths"),
  });
  return (
    <div>
      <h1 className="text-3xl font-semibold tracking-tight">Curriculum</h1>
      <p className="mt-2 max-w-2xl text-slate-600 dark:text-slate-300">
        Paths are seeded from the catalog module. Publishing a library resource does not insert it
        into a path. Path edits remain a catalog change.
      </p>
      {query.isLoading ? <p className="mt-6">Loading curriculum…</p> : null}
      {query.data && query.data.length === 0 ? (
        <p className="mt-6">No studio tracks yet. Run <code>make migrate</code>.</p>
      ) : null}
      <div className="mt-6 grid gap-4 md:grid-cols-2">
        {(query.data || []).map((path) => (
          <article
            key={path.slug}
            className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900"
          >
            <p className="text-xs font-semibold uppercase tracking-wide text-[#1d4ed8]">{path.level}</p>
            <h2 className="text-xl font-semibold">
              <Link className="underline" href={`/curriculum/${path.slug}`}>
                {path.title}
              </Link>
            </h2>
            <p className="mt-2 text-sm text-slate-700 dark:text-slate-300">{path.description}</p>
            <p className="mt-2 text-sm">{path.concepts} concepts</p>
          </article>
        ))}
      </div>
    </div>
  );
}
