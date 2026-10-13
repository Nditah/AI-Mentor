"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { api } from "@/lib/api";

type Node = { slug: string; name: string };

export default function GeneratePage() {
  const client = useQueryClient();
  const graph = useQuery({
    queryKey: ["graph"],
    queryFn: () => api<{ nodes: Node[] }>("/api/v1/knowledge-graph"),
  });
  const [slug, setSlug] = useState("q-learning");
  const [created, setCreated] = useState<string | null>(null);
  const generate = useMutation({
    mutationFn: () =>
      api<{ id: string; title: string }>("/api/v1/admin/assets/generate", {
        method: "POST",
        body: JSON.stringify({ concept_slug: slug }),
      }),
    onSuccess: (asset) => {
      setCreated(asset.id);
      client.invalidateQueries({ queryKey: ["assets"] });
    },
  });

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    generate.mutate();
  }

  return (
    <form className="max-w-xl" onSubmit={onSubmit}>
      <h1 className="text-3xl font-semibold tracking-tight">Generate</h1>
      <p className="mt-2 text-slate-600 dark:text-slate-300">
        This drafts notes from the catalog scaffold. It does not call a model, and the draft stays in the library until someone reviews it.
      </p>
      <label className="mt-4 block text-sm font-semibold">
        Concept
        <select className="mt-1 w-full rounded-full border border-slate-300 bg-white px-3 py-2 dark:border-slate-600 dark:bg-slate-950" value={slug} onChange={(event) => setSlug(event.target.value)}>
          {(graph.data?.nodes || [{ slug: "q-learning", name: "Q-learning" }]).map((node) => (
            <option key={node.slug} value={node.slug}>
              {node.name}
            </option>
          ))}
        </select>
      </label>
      <button className="mt-4 rounded-full bg-[#1d4ed8] px-4 py-2 font-semibold text-white" type="submit">
        Create draft
      </button>
      {created ? (
        <p className="mt-3">
          Draft ready. <a className="underline" href={`/library/${created}`}>Open it</a>
        </p>
      ) : null}
      {generate.error ? <p className="mt-2 text-red-800 dark:text-red-300">{generate.error.message}</p> : null}
    </form>
  );
}
