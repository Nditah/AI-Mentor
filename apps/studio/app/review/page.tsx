"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";

type Asset = { id: string; title: string; topic: string; author_name: string };

export default function ReviewPage() {
  const client = useQueryClient();
  const query = useQuery({
    queryKey: ["review"],
    queryFn: () => api<Asset[]>("/api/v1/content/assets?state=review"),
  });
  const move = useMutation({
    mutationFn: ({ id, state }: { id: string; state: "approved" | "draft" }) =>
      api(`/api/v1/content/assets/${id}/transition`, {
        method: "POST",
        body: JSON.stringify({ state, note: state === "approved" ? "Approved from the queue" : "Sent back from the queue" }),
      }),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["review"] });
      client.invalidateQueries({ queryKey: ["assets"] });
      client.invalidateQueries({ queryKey: ["studio-home"] });
      client.invalidateQueries({ queryKey: ["overview"] });
    },
  });
  return (
    <div>
      <h1 className="text-3xl font-semibold tracking-tight">Review queue</h1>
      <p className="mt-2 max-w-2xl text-slate-600 dark:text-slate-300">
        An instructor cannot approve a resource they submitted. An admin can, and the audit log marks that as self-approved.
      </p>
      {query.data?.length === 0 ? <p className="mt-6">Nothing is waiting for review.</p> : null}
      {move.error ? (
        <p className="mt-4 text-sm text-red-800 dark:text-red-300">
          {move.error instanceof ApiError ? move.error.message : move.error.message}
        </p>
      ) : null}
      <ul className="mt-6 space-y-3">
        {(query.data || []).map((asset) => (
          <li key={asset.id} className="rounded-2xl border border-slate-200 p-4 dark:border-slate-700">
            <Link className="font-semibold underline" href={`/library/${asset.id}`}>
              {asset.title}
            </Link>
            <p className="text-sm text-slate-600 dark:text-slate-300">
              {asset.topic || "No topic"} · {asset.author_name}
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <button
                className="rounded-full bg-[#1d4ed8] px-3 py-1.5 text-sm font-semibold text-white"
                type="button"
                disabled={move.isPending}
                onClick={() => move.mutate({ id: asset.id, state: "approved" })}
              >
                Approve
              </button>
              <button
                className="rounded-full border border-slate-300 px-3 py-1.5 text-sm font-semibold dark:border-slate-600"
                type="button"
                disabled={move.isPending}
                onClick={() => move.mutate({ id: asset.id, state: "draft" })}
              >
                Send back
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
