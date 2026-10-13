"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

type Node = { slug: string; name: string; domain: string; difficulty: string; prerequisites: string[] };

export default function TaxonomyPage() {
  const query = useQuery({
    queryKey: ["taxonomy"],
    queryFn: () => api<Node[]>("/api/v1/content/taxonomy"),
  });
  const nodes = query.data || [];
  const domains = [...new Set(nodes.map((node) => node.domain))];
  return (
    <div>
      <h1 className="text-3xl font-semibold tracking-tight">Taxonomy</h1>
      <p className="mt-2 max-w-2xl text-slate-600 dark:text-slate-300">
        The tree is the catalog. Recommendations use these prerequisites. A draft change set is not stored yet.
      </p>
      <div className="mt-6 space-y-6">
        {domains.map((domain) => (
          <section key={domain}>
            <h2 className="text-xl font-semibold">{domain}</h2>
            <ul className="mt-2 space-y-1 text-sm">
              {nodes
                .filter((node) => node.domain === domain)
                .map((node) => (
                  <li key={node.slug}>
                    <span className="font-semibold">{node.name}</span>
                    <span className="text-slate-600 dark:text-slate-300">
                      {" "}
                      · {node.difficulty}
                      {node.prerequisites.length ? ` · needs ${node.prerequisites.join(", ")}` : ""}
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
