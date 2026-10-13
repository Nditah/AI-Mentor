"use client";

import { useQuery } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { api } from "@/lib/api";

type Item = {
  id: string;
  title: string;
  description: string;
  resource_type_label: string;
  difficulty: string;
  provider: string;
  url: string | null;
  quality_score: number;
  reason?: string;
};

type Page = { items: Item[] };
type Recs = { resources: Item[]; concepts: { slug: string; name: string; reason?: string }[] };

export default function CatalogPage() {
  const [params, setParams] = useState("limit=20");
  const listing = useQuery({
    queryKey: ["catalog", params],
    queryFn: () => api<Page>(`/api/v1/resources?${params}`),
  });
  const recs = useQuery({
    queryKey: ["catalog-recs"],
    queryFn: () => api<Recs>("/api/v1/catalog/recommendations"),
  });

  function onSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const next = new URLSearchParams();
    const q = String(data.get("q") || "").trim();
    const type = String(data.get("type") || "");
    const difficulty = String(data.get("difficulty") || "");
    if (q) next.set("q", q);
    if (type) next.set("resource_type", type);
    if (difficulty) next.set("difficulty", difficulty);
    next.set("limit", "20");
    setParams(next.toString());
  }

  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="font-display text-4xl tracking-tight">Catalog</h1>
      <p className="mt-2 max-w-2xl text-slate-600 dark:text-slate-300">
        Search published books, papers, courses, videos, datasets, and repositories. Ranking
        follows your style, goal academy, and free-only setting from{" "}
        <a className="font-semibold text-[#1d4ed8] underline" href="/settings">
          Settings
        </a>
        .
      </p>
      <form className="mt-6 flex flex-wrap gap-2" onSubmit={onSearch}>
        <input
          name="q"
          placeholder="Bellman equation, transformers, ROS 2…"
          className="min-w-[16rem] flex-1 rounded-full border border-slate-300 px-4 py-2 dark:border-slate-600 dark:bg-slate-900"
        />
        <select name="type" className="rounded-full border border-slate-300 px-3 py-2 dark:border-slate-600 dark:bg-slate-900">
          <option value="">Any type</option>
          <option value="book">Book</option>
          <option value="paper">Paper</option>
          <option value="course">Course</option>
          <option value="video">Video</option>
          <option value="repository">Repository</option>
          <option value="dataset">Dataset</option>
        </select>
        <select name="difficulty" className="rounded-full border border-slate-300 px-3 py-2 dark:border-slate-600 dark:bg-slate-900">
          <option value="">Any difficulty</option>
          <option value="beginner">Beginner</option>
          <option value="intermediate">Intermediate</option>
          <option value="advanced">Advanced</option>
        </select>
        <button className="rounded-full bg-[#1d4ed8] px-4 py-2 text-sm font-semibold text-white" type="submit">
          Search
        </button>
      </form>
      {recs.data?.resources?.length ? (
        <section className="mt-8">
          <h2 className="text-xl font-semibold">Recommended for you</h2>
          <ul className="mt-3 space-y-2">
            {recs.data.resources.slice(0, 4).map((item) => (
              <li key={item.id} className="rounded-2xl border border-slate-200 p-4 dark:border-slate-700">
                <p className="font-semibold">{item.title}</p>
                <p className="text-sm text-slate-600 dark:text-slate-300">{item.reason}</p>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
      <section className="mt-8">
        <h2 className="text-xl font-semibold">Results</h2>
        {listing.isLoading ? <p className="mt-3">Searching…</p> : null}
        <ul className="mt-3 space-y-3">
          {(listing.data?.items || []).map((item) => (
            <li key={item.id} className="rounded-2xl border border-slate-200 p-4 dark:border-slate-700">
              <p className="text-xs font-semibold uppercase tracking-wide text-[#1d4ed8]">
                {item.resource_type_label} · {item.difficulty}
              </p>
              <h3 className="text-lg font-semibold">{item.title}</h3>
              <p className="mt-1 text-sm text-slate-700 dark:text-slate-300">{item.description}</p>
              <p className="mt-2 text-sm">
                {item.provider || "Unknown provider"} · quality {item.quality_score}
                {item.url ? (
                  <>
                    {" · "}
                    <a className="underline" href={item.url} rel="noreferrer" target="_blank">
                      Open source
                    </a>
                  </>
                ) : null}
              </p>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
