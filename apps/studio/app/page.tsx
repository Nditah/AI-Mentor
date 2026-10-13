"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";

type Home = {
  published: number;
  pack_published: number;
  drafts: number;
  review_queue: number;
  questions: number;
  challenges: number;
  by_type: Record<string, number>;
  workspace: string;
  note: string;
};

export default function StudioHomePage() {
  const query = useQuery({
    queryKey: ["studio-home"],
    queryFn: () => api<Home>("/api/v1/content/home"),
    retry: false,
  });
  if (query.error instanceof ApiError) return <p>{query.error.message}</p>;
  if (!query.data) return <p>Loading Content Studio…</p>;
  const data = query.data;
  const tiles = [
    ["Published catalog", data.published, "/catalog"],
    ["Knowledge Pack", data.pack_published, "/catalog"],
    ["Library drafts", data.drafts, "/library"],
    ["In review", data.review_queue, "/review"],
    ["Question bank", data.questions, "/studio/assessments"],
    ["Challenges", data.challenges, "/challenges"],
  ] as const;
  const types = Object.entries(data.by_type || {}).sort((left, right) => right[1] - left[1]);
  return (
    <div>
      <h1 className="text-3xl font-semibold tracking-tight">Content Studio</h1>
      <p className="mt-2 max-w-2xl text-slate-600 dark:text-slate-300">
        Workspace <span className="font-semibold">{data.workspace}</span>. {data.note}
      </p>
      <dl className="mt-6 grid gap-3 sm:grid-cols-3">
        {tiles.map(([label, value, href]) => (
          <Link
            key={label}
            href={href}
            className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900"
          >
            <dt className="text-sm text-slate-600 dark:text-slate-300">{label}</dt>
            <dd className="text-3xl font-semibold">{value}</dd>
          </Link>
        ))}
      </dl>
      {types.length ? (
        <section className="mt-8">
          <h2 className="text-xl font-semibold">Published by type</h2>
          <ul className="mt-3 columns-2 text-sm">
            {types.map(([type, count]) => (
              <li key={type}>
                <Link className="underline" href={`/catalog?type=${encodeURIComponent(type)}`}>
                  {type}
                </Link>
                {` · ${count}`}
              </li>
            ))}
          </ul>
        </section>
      ) : (
        <p className="mt-8">
          No catalog rows yet. Run <code>make seed-pack</code> or import JSON.
        </p>
      )}
      <ul className="mt-8 space-y-2">
        <li>
          <Link className="underline" href="/catalog/import">
            Import centre
          </Link>
        </li>
        <li>
          <Link className="underline" href="/catalog/quality">
            Quality scores
          </Link>
        </li>
        <li>
          <Link className="underline" href="/catalog/duplicates">
            Duplicate detection
          </Link>
        </li>
        <li>
          <Link className="underline" href="/graph">
            Knowledge graph
          </Link>
        </li>
      </ul>
    </div>
  );
}
