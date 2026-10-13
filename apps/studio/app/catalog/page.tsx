"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useEffect, useState } from "react";
import { api } from "@/lib/api";

type Item = {
  id: string;
  title: string;
  resource_type: string;
  resource_type_label: string;
  category: string;
  difficulty: string;
  provider: string;
  quality_score: number;
  url: string | null;
};

type Page = { items: Item[] };

const types = [
  ["", "All types"],
  ["book", "Book"],
  ["paper", "Paper"],
  ["video", "Video"],
  ["course", "Course"],
  ["repository", "Repository"],
  ["dataset", "Dataset"],
  ["tutorial", "Tutorial"],
  ["blog", "Blog"],
  ["certification", "Certification"],
  ["documentation", "Documentation"],
  ["podcast", "Podcast"],
  ["learning_path", "Learning path"],
  ["coding_challenge", "Coding challenge"],
];

export default function CatalogPage() {
  return (
    <Suspense fallback={<p>Loading the catalog…</p>}>
      <CatalogBrowser />
    </Suspense>
  );
}

function CatalogBrowser() {
  const router = useRouter();
  const params = useSearchParams();
  const q = params.get("q") || "";
  const type = params.get("type") || "";
  const [draftQ, setDraftQ] = useState(q);
  const [draftType, setDraftType] = useState(type);
  useEffect(() => {
    setDraftQ(q);
    setDraftType(type);
  }, [q, type]);
  const query = useQuery({
    queryKey: ["catalog", q, type],
    queryFn: () => {
      const search = new URLSearchParams();
      if (q) search.set("q", q);
      if (type) search.set("resource_type", type);
      search.set("limit", "100");
      return api<Page>(`/api/v1/resources?${search.toString()}`);
    },
  });
  const items = query.data?.items || [];

  function onSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const search = new URLSearchParams();
    if (draftQ) search.set("q", draftQ);
    if (draftType) search.set("type", draftType);
    const queryString = search.toString();
    router.push(queryString ? `/catalog?${queryString}` : "/catalog");
  }

  return (
    <div>
      <h1 className="text-3xl font-semibold tracking-tight">Resource catalog</h1>
      <p className="mt-2 max-w-2xl text-slate-600 dark:text-slate-300">
        Published Knowledge Pack and imported records. Drafts stay in the library until an admin
        publishes them.
      </p>
      <form className="mt-4 flex flex-wrap gap-2" onSubmit={onSearch}>
        <input
          name="q"
          value={draftQ}
          onChange={(event) => setDraftQ(event.target.value)}
          placeholder="Topic, skill, or title"
          className="rounded-full border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-900"
        />
        <select
          name="type"
          value={draftType}
          onChange={(event) => setDraftType(event.target.value)}
          className="rounded-full border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-900"
        >
          {types.map(([value, label]) => (
            <option key={value || "all"} value={value}>
              {label}
            </option>
          ))}
        </select>
        <button className="rounded-full bg-[#1d4ed8] px-4 py-2 text-sm font-semibold text-white" type="submit">
          Search
        </button>
        <Link
          className="rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold dark:border-slate-600"
          href="/catalog/import"
        >
          Import
        </Link>
      </form>
      {query.isLoading ? <p className="mt-6">Loading the catalog…</p> : null}
      {items.length === 0 && query.data ? (
        <p className="mt-6">No published resources match. Seed the Knowledge Pack or import JSON.</p>
      ) : null}
      <div className="mt-6 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <caption className="sr-only">Published catalog</caption>
          <thead>
            <tr className="border-b border-slate-200 dark:border-slate-700">
              <th className="py-2">Title</th>
              <th>Type</th>
              <th>Category</th>
              <th>Provider</th>
              <th>Quality</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id} className="border-b border-slate-100 dark:border-slate-800">
                <td className="py-2">
                  <Link className="font-semibold underline" href={`/catalog/${item.id}`}>
                    {item.title}
                  </Link>
                  <span className="block text-slate-500">{item.difficulty}</span>
                </td>
                <td>{item.resource_type_label}</td>
                <td>{item.category}</td>
                <td>{item.provider || "—"}</td>
                <td>{item.quality_score}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
