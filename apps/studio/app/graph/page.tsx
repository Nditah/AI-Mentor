"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { api } from "@/lib/api";

type Node = { slug: string; name: string; category: string; difficulty: string; summary: string };
type Edge = { source: string; target: string; relation_type: string; weight: number };
type Graph = { nodes: Node[]; edges: Edge[]; mermaid: string };
type Facets = { taxonomy: { slug: string; name: string; level: string }[] };

export default function GraphPage() {
  const [category, setCategory] = useState("");
  const facets = useQuery({
    queryKey: ["facets"],
    queryFn: () => api<Facets>("/api/v1/catalog/facets"),
  });
  const query = useQuery({
    queryKey: ["catalog-graph", category],
    queryFn: () => {
      const params = category ? `?category=${encodeURIComponent(category)}` : "";
      return api<Graph>(`/api/v1/catalog/graph${params}`);
    },
  });
  const categories = useMemo(() => {
    const fromTaxonomy = (facets.data?.taxonomy || [])
      .filter((node) => node.level === "category")
      .map((node) => node.slug);
    if (fromTaxonomy.length) return fromTaxonomy;
    return [...new Set((query.data?.nodes || []).map((node) => node.category).filter(Boolean))].sort();
  }, [facets.data, query.data]);
  const data = query.data;
  return (
    <div>
      <h1 className="text-3xl font-semibold tracking-tight">Knowledge graph</h1>
      <p className="mt-2 max-w-2xl text-slate-600 dark:text-slate-300">
        Typed relations among concepts. A cycle on prerequisite_of is refused at seed time. This
        graph powers recommendations; instructors consume it, they do not edit master here.
      </p>
      <label className="mt-4 block max-w-xs text-sm font-semibold">
        Category
        <select
          className="mt-1 w-full rounded-full border border-slate-300 bg-white px-3 py-2 dark:border-slate-600 dark:bg-slate-950"
          value={category}
          onChange={(event) => setCategory(event.target.value)}
        >
          <option value="">All categories</option>
          {categories.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
      </label>
      {data ? (
        <p className="mt-3 text-sm">
          {data.nodes.length} concepts · {data.edges.length} relations
        </p>
      ) : (
        <p className="mt-6">Loading the graph…</p>
      )}
      {category ? (
        <pre className="mt-4 overflow-x-auto rounded-2xl bg-white p-4 text-sm dark:bg-slate-900">
          {data?.mermaid || ""}
        </pre>
      ) : (
        <p className="mt-4 text-sm text-slate-600 dark:text-slate-300">
          Choose a category to render the Mermaid diagram. The full pack graph is too large to draw
          at once.
        </p>
      )}
      <h2 className="mt-8 text-xl font-semibold">Relations</h2>
      <ul className="mt-2 max-h-96 overflow-y-auto text-sm">
        {(data?.edges || []).slice(0, 80).map((edge) => (
          <li key={`${edge.source}-${edge.relation_type}-${edge.target}`}>
            <span className="font-semibold">{edge.source}</span>
            {` —${edge.relation_type}→ `}
            <span className="font-semibold">{edge.target}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
