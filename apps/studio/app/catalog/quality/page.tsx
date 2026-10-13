"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

type Item = {
  id: string;
  title: string;
  resource_type_label: string;
  provider: string;
  quality_score: number;
  difficulty: string;
};

type Page = { items: Item[] };
type Overview = { published: number; by_type: Record<string, number> };

export default function QualityPage() {
  const overview = useQuery({
    queryKey: ["catalog-overview"],
    queryFn: () => api<Overview>("/api/v1/admin/catalog/overview"),
  });
  const listing = useQuery({
    queryKey: ["catalog-quality"],
    queryFn: () => api<Page>("/api/v1/resources?limit=50"),
  });
  const items = [...(listing.data?.items || [])].sort(
    (left, right) => left.quality_score - right.quality_score,
  );
  return (
    <div>
      <h1 className="text-3xl font-semibold tracking-tight">Content quality</h1>
      <p className="mt-2 max-w-2xl text-slate-600 dark:text-slate-300">
        Completeness, provenance, usefulness, freshness, and verification on a 0–100 scorecard. Lowest scores first.
      </p>
      {overview.data ? (
        <p className="mt-4 text-sm">
          {overview.data.published} published records
          {Object.entries(overview.data.by_type || {})
            .map(([type, count]) => ` · ${type} ${count}`)
            .join("")}
        </p>
      ) : null}
      <ol className="mt-6 space-y-2">
        {items.map((item) => (
          <li key={item.id} className="rounded-2xl border border-slate-200 p-3 text-sm dark:border-slate-700">
            <span className="font-semibold">{item.quality_score}</span>
            {" · "}
            <span>{item.title}</span>
            <span className="block text-slate-600 dark:text-slate-300">
              {item.resource_type_label} · {item.provider || "unknown"} · {item.difficulty}
            </span>
          </li>
        ))}
      </ol>
    </div>
  );
}
