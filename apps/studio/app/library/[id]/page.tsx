"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { use } from "react";
import { api } from "@/lib/api";

type Asset = {
  id: string;
  title: string;
  description: string;
  state: string;
  kind: string;
  difficulty: string;
  topic: string;
  version: number;
  body_md: string;
  chunks: number;
  tags: string[];
  licence: string;
  author_name: string;
  estimated_minutes: number;
  versions: { version: number; state: string; change_note: string; created_at: string }[];
};

const next: Record<string, string[]> = {
  draft: ["review"],
  review: ["approved", "draft"],
  approved: ["published", "draft"],
  published: ["archived", "draft"],
  archived: ["draft"],
};

export default function AssetPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const client = useQueryClient();
  const query = useQuery({
    queryKey: ["asset", id],
    queryFn: () => api<Asset>(`/api/v1/content/assets/${id}`),
  });
  const move = useMutation({
    mutationFn: (state: string) =>
      api(`/api/v1/content/assets/${id}/transition`, {
        method: "POST",
        body: JSON.stringify({ state, note: "" }),
      }),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["asset", id] });
      client.invalidateQueries({ queryKey: ["assets"] });
      client.invalidateQueries({ queryKey: ["overview"] });
      client.invalidateQueries({ queryKey: ["studio-home"] });
      client.invalidateQueries({ queryKey: ["review"] });
    },
  });
  if (!query.data) return <p>Loading the resource…</p>;
  const asset = query.data;
  return (
    <article className="max-w-3xl">
      <p className="text-sm font-semibold uppercase tracking-wide text-[#1d4ed8]">{asset.state} · v{asset.version}</p>
      <h1 className="mt-1 text-3xl font-semibold tracking-tight">{asset.title}</h1>
      <p className="mt-2 text-slate-700 dark:text-slate-300">{asset.description}</p>
      <p className="mt-2 text-sm">
        {asset.kind} · {asset.difficulty} · {asset.estimated_minutes} min · {asset.topic || "No topic"} · {asset.licence}
      </p>
      <p className="text-sm">Author {asset.author_name}. Indexed chunks: {asset.chunks}.</p>
      {asset.state === "published" ? (
        <p className="mt-2 text-sm">Starting a revision moves this copy back to draft until an admin publishes it again.</p>
      ) : null}
      <div className="mt-4 flex flex-wrap gap-2">
        {(next[asset.state] || []).map((state) => (
          <button
            key={state}
            className="rounded-full border border-slate-300 px-3 py-2 text-sm font-semibold dark:border-slate-600"
            type="button"
            onClick={() => move.mutate(state)}
          >
            Move to {state}
          </button>
        ))}
      </div>
      {move.error ? <p className="mt-2 text-red-800 dark:text-red-300">{move.error.message}</p> : null}
      <h2 className="mt-8 text-xl font-semibold">Content</h2>
      <pre className="mt-2 whitespace-pre-wrap rounded-2xl bg-white p-4 text-sm dark:bg-slate-900">{asset.body_md || "No body yet."}</pre>
      <h2 className="mt-8 text-xl font-semibold">Versions</h2>
      <ul className="mt-2 space-y-1 text-sm">
        {asset.versions.map((version) => (
          <li key={`${version.version}-${version.created_at}`}>
            v{version.version} · {version.state} · {version.change_note || "No note"}
          </li>
        ))}
      </ul>
    </article>
  );
}
