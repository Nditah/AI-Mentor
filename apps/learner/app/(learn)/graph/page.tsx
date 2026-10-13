"use client";

import { useQuery } from "@tanstack/react-query";
import { MentorMarkdown } from "@/components/markdown-view";
import { api } from "@/lib/api";

type Graph = {
  mermaid: string;
  nodes: { slug: string; name: string; domain: string; difficulty: string; prerequisites: string[] }[];
};

export default function GraphPage() {
  const query = useQuery({
    queryKey: ["graph"],
    queryFn: () => api<Graph>("/api/v1/knowledge-graph"),
  });
  const nodes = query.data?.nodes || [];
  const domains = [...new Set(nodes.map((node) => node.domain))];
  return (
    <div>
      <h1 className="font-display text-4xl tracking-tight">Concept map</h1>
      <p className="mt-2 max-w-2xl text-slate-700 dark:text-slate-300">
        An arrow means the left concept is a prerequisite of the right one. The list below is the accessible version of the same graph.
      </p>
      {query.data ? (
        <div className="mt-6 rounded-3xl bg-white p-4 dark:bg-slate-900">
          <MentorMarkdown content={"```mermaid\n" + query.data.mermaid + "\n```"} />
        </div>
      ) : (
        <p className="mt-6">Loading the map…</p>
      )}
      <div className="mt-8 space-y-6">
        {domains.map((domain) => (
          <section key={domain}>
            <h2 className="text-xl font-semibold">{domain}</h2>
            <ul className="mt-2 space-y-1">
              {nodes
                .filter((node) => node.domain === domain)
                .map((node) => (
                  <li key={node.slug}>
                    <span className="font-semibold">{node.name}</span>
                    <span className="text-slate-600 dark:text-slate-300">
                      {" "}
                      · {node.difficulty}
                      {node.prerequisites.length ? ` · needs ${node.prerequisites.join(", ")}` : " · starts a branch"}
                    </span>
                  </li>
                ))}
            </ul>
          </section>
        ))}
      </div>
    </div>
  );
}
