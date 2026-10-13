"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export default function GraphPage() {
  const query = useQuery({
    queryKey: ["graph"],
    queryFn: () => api<{ mermaid: string }>(`/api/v1/knowledge-graph`),
  });
  return (
    <div>
      <h1 className="text-3xl font-semibold tracking-tight">Knowledge graph</h1>
      <p className="mt-2 max-w-2xl text-slate-600 dark:text-slate-300">
        An arrow means the left concept is a prerequisite of the right one. The same graph powers recommendations.
      </p>
      <pre className="mt-6 overflow-x-auto rounded-2xl bg-white p-4 text-sm dark:bg-slate-900">{query.data?.mermaid || "Loading the graph…"}</pre>
    </div>
  );
}
