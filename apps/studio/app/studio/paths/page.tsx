"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { api } from "@/lib/api";

type CatalogPath = {
  id: string;
  title: string;
  description: string;
  concepts: string[];
  difficulty: string;
};

type PathCard = { slug: string; title: string; description: string; level: string; concepts: number };

export default function PathBuilderPage() {
  const query = useQuery({
    queryKey: ["catalog-paths"],
    queryFn: () =>
      api<{ items: CatalogPath[] }>("/api/v1/resources?resource_type=learning_path&limit=100"),
  });
  const curriculum = useQuery({
    queryKey: ["paths"],
    queryFn: () => api<PathCard[]>("/api/v1/learning-paths"),
  });
  return (
    <div>
      <h1 className="text-3xl font-semibold tracking-tight">Learning path builder</h1>
      <p className="mt-2 max-w-2xl text-slate-600 dark:text-slate-300">
        Catalog paths are ordered concept lists from the Knowledge Pack. Curriculum paths below are
        the four studio tracks seeded from the catalog module. Full lesson and course editors remain
        a later release.
      </p>
      <h2 className="mt-8 text-xl font-semibold">Catalog paths</h2>
      {query.isLoading ? <p className="mt-3">Loading paths…</p> : null}
      {query.data && query.data.items.length === 0 ? (
        <p className="mt-3">No catalog paths yet. Seed the Knowledge Pack.</p>
      ) : null}
      <div className="mt-3 grid gap-4 md:grid-cols-2">
        {(query.data?.items || []).map((path) => (
          <article
            key={path.id}
            className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900"
          >
            <p className="text-xs font-semibold uppercase tracking-wide text-[#1d4ed8]">
              {path.difficulty}
            </p>
            <h3 className="text-lg font-semibold">
              <Link className="underline" href={`/catalog/${path.id}`}>
                {path.title}
              </Link>
            </h3>
            <p className="mt-2 text-sm">{path.description}</p>
            <p className="mt-2 text-sm">{path.concepts?.length || 0} concepts</p>
          </article>
        ))}
      </div>
      <h2 className="mt-8 text-xl font-semibold">Studio curriculum</h2>
      <ul className="mt-2 space-y-1 text-sm">
        {(curriculum.data || []).map((path) => (
          <li key={path.slug}>
            <Link className="font-semibold underline" href={`/curriculum/${path.slug}`}>
              {path.title}
            </Link>
            {` · ${path.concepts} lessons`}
          </li>
        ))}
      </ul>
    </div>
  );
}
