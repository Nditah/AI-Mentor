"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

type Hit = {
  id: string;
  titles: string[];
  method: string;
  score: number;
  status: string;
};

export default function DuplicatesPage() {
  const client = useQueryClient();
  const query = useQuery({
    queryKey: ["duplicates"],
    queryFn: () => api<Hit[]>("/api/v1/content/catalog/duplicates"),
  });
  const resolve = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      api(`/api/v1/content/catalog/duplicates/${id}`, { method: "POST", body: JSON.stringify({ status }) }),
    onSuccess: () => client.invalidateQueries({ queryKey: ["duplicates"] }),
  });
  return (
    <div>
      <h1 className="text-3xl font-semibold tracking-tight">Duplicate detection</h1>
      <p className="mt-2 max-w-2xl text-slate-600 dark:text-slate-300">
        URL, DOI, and title overlap. Merging archives the first record and keeps the second.
      </p>
      <ul className="mt-6 space-y-3">
        {(query.data || []).map((hit) => (
          <li key={hit.id} className="rounded-2xl border border-slate-200 p-4 dark:border-slate-700">
            <p className="font-semibold">{hit.titles.join(" · ")}</p>
            <p className="text-sm">{hit.method} · score {hit.score} · {hit.status}</p>
            {hit.status === "open" ? (
              <div className="mt-2 flex gap-2">
                <button className="rounded-full border border-slate-300 px-3 py-1 text-sm dark:border-slate-600" type="button" onClick={() => resolve.mutate({ id: hit.id, status: "dismissed" })}>
                  Dismiss
                </button>
                <button className="rounded-full bg-[#1d4ed8] px-3 py-1 text-sm text-white" type="button" onClick={() => resolve.mutate({ id: hit.id, status: "merged" })}>
                  Merge
                </button>
              </div>
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}
