"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { use } from "react";
import { api } from "@/lib/api";
import { useStudio } from "@/stores/studio";

type PathCard = {
  slug: string;
  title: string;
  description: string;
  level: string;
  progress: number;
  locked: boolean;
};

export default function AcademyPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = use(params);
  const devUserId = useStudio((state) => state.devUserId);
  const query = useQuery({
    queryKey: ["academy", slug, devUserId],
    queryFn: () => api<{ title: string; summary: string; progress: number; paths: PathCard[] }>(`/api/v1/learn/academies/${slug}`),
  });
  if (query.isLoading) return <p>Loading the academy…</p>;
  if (!query.data) return <p>That academy was not found.</p>;
  const academy = query.data;
  return (
    <div>
      <p className="text-sm">
        <Link className="underline" href="/academies">Academies</Link>
      </p>
      <h1 className="mt-2 font-display text-4xl tracking-tight">{academy.title}</h1>
      <p className="mt-2 max-w-2xl text-slate-700 dark:text-slate-300">{academy.summary}</p>
      <p className="mt-2 text-sm font-semibold">{academy.progress}% of this academy</p>
      <ol className="mt-6 space-y-4">
        {academy.paths.map((path, index) => (
          <li key={path.slug} className="rounded-3xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900">
            <p className="text-xs font-semibold uppercase tracking-wide text-[#1d4ed8]">
              Path {index + 1} · {path.level} · {path.progress}%
            </p>
            <h2 className="mt-1 text-2xl font-semibold">
              {path.locked ? path.title : <Link className="underline" href={`/paths/${path.slug}`}>{path.title}</Link>}
            </h2>
            <p className="mt-2 text-slate-700 dark:text-slate-300">{path.description}</p>
            {path.locked ? <p className="mt-2 text-sm">Finish the previous path to open this one.</p> : null}
          </li>
        ))}
      </ol>
    </div>
  );
}
