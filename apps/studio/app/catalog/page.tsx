"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";
import { api } from "@/lib/api";

type Item = {
  id: string;
  title: string;
  resource_type_label: string;
  category: string;
  difficulty: string;
  provider: string;
  quality_score: number;
  url: string | null;
};

type Page = { items: Item[] };

export default function CatalogPage() {
  const [q, setQ] = useState("");
  const [type, setType] = useState("");
  const query = useQuery({
    queryKey: ["catalog", q, type],
    queryFn: () => {
      const params = new URLSearchParams();
      if (q) params.set("q", q);
      if (type) params.set("resource_type", type);
      params.set("limit", "50");
      return api<Page>(`/api/v1/resources?${params.toString()}`);
    },
  });
  const items = query.data?.items || [];
  return (
    <div>
      <h1 className="text-3xl font-semibold tracking-tight">Resource catalog</h1>
      <p className="mt-2 max-w-2xl text-slate-600 dark:text-slate-300">
        Published Knowledge Pack and imported records. Drafts stay in the library until an admin publishes them.
      </p>
      <form
        className="mt-4 flex flex-wrap gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          const data = new FormData(event.currentTarget);
          setQ(String(data.get("q") || ""));
          setType(String(data.get("type") || ""));
        }}
      >
        <input name="q" defaultValue={q} placeholder="Topic, skill, or title" className="rounded-full border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-900" />
        <select name="type" defaultValue={type} className="rounded-full border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-900">
          <option value="">All types</option>
          <option value="book">Book</option>
          <option value="paper">Paper</option>
          <option value="video">Video</option>
          <option value="course">Course</option>
          <option value="repository">Repository</option>
          <option value="dataset">Dataset</option>
          <option value="certification">Certification</option>
        </select>
        <button className="rounded-full bg-[#1d4ed8] px-4 py-2 text-sm font-semibold text-white" type="submit">
          Search
        </button>
        <Link className="rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold dark:border-slate-600" href="/catalog/import">
          Import
        </Link>
      </form>
      {query.isLoading ? <p className="mt-6">Loading the catalog…</p> : null}
      {items.length === 0 && query.data ? <p className="mt-6">No published resources match. Seed the Knowledge Pack or import a JSON file.</p> : null}
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
                  <span className="font-semibold">{item.title}</span>
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
