"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { api, ApiError } from "@/lib/api";

type Source = { slug: string; name: string; provider: string; status: string; last_error: string; terms_note: string };
type Job = { id: string; kind: string; status: string; stats: Record<string, number>; created_at: string };

export default function ImportPage() {
  const [note, setNote] = useState("");
  const sources = useQuery({ queryKey: ["sources"], queryFn: () => api<Source[]>("/api/v1/content/catalog/sources") });
  const jobs = useQuery({ queryKey: ["jobs"], queryFn: () => api<Job[]>("/api/v1/content/catalog/jobs") });
  const upload = useMutation({
    mutationFn: async (resources: unknown[]) =>
      api("/api/v1/content/catalog/import", { method: "POST", body: JSON.stringify({ source: "curated-pack", resources }) }),
    onSuccess: () => {
      setNote("Import finished. Check the job log.");
      jobs.refetch();
    },
    onError: (error) => setNote(error instanceof ApiError ? error.message : "Import failed."),
  });
  const refresh = useMutation({
    mutationFn: (slug: string) => api(`/api/v1/content/catalog/sources/${slug}/refresh`, { method: "POST" }),
    onSuccess: () => sources.refetch(),
  });

  async function onFile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const input = event.currentTarget.elements.namedItem("file") as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) {
      setNote("Choose a JSON file first.");
      return;
    }
    const parsed = JSON.parse(await file.text()) as unknown;
    const resources = Array.isArray(parsed) ? parsed : (parsed as { resources?: unknown[] }).resources;
    if (!Array.isArray(resources)) {
      setNote("The file must be an array, or an object with a resources array.");
      return;
    }
    upload.mutate(resources);
  }

  return (
    <div className="max-w-3xl">
      <h1 className="text-3xl font-semibold tracking-tight">Asset import centre</h1>
      <p className="mt-2 text-slate-600 dark:text-slate-300">
        Bulk JSON goes through the twelve-stage ingestion pipeline. Remote harvests stay paused until a connector token is set.
      </p>
      <form className="mt-6 space-y-3" onSubmit={onFile}>
        <label className="block text-sm font-semibold">
          JSON file
          <input className="mt-1 block" name="file" type="file" accept="application/json" />
        </label>
        <button className="rounded-full bg-[#1d4ed8] px-4 py-2 text-sm font-semibold text-white" type="submit">
          Import
        </button>
      </form>
      {note ? <p className="mt-3 text-sm">{note}</p> : null}
      <h2 className="mt-8 text-xl font-semibold">Sources</h2>
      <ul className="mt-2 space-y-2 text-sm">
        {(sources.data || []).map((source) => (
          <li key={source.slug} className="rounded-2xl border border-slate-200 p-3 dark:border-slate-700">
            <p className="font-semibold">{source.name}</p>
            <p className="text-slate-600 dark:text-slate-300">{source.provider} · {source.status}</p>
            <p className="mt-1">{source.terms_note}</p>
            {source.last_error ? <p className="mt-1 text-red-800 dark:text-red-300">{source.last_error}</p> : null}
            <button className="mt-2 rounded-full border border-slate-300 px-3 py-1 dark:border-slate-600" type="button" onClick={() => refresh.mutate(source.slug)}>
              Refresh
            </button>
          </li>
        ))}
      </ul>
      <h2 className="mt-8 text-xl font-semibold">Import logs</h2>
      <ul className="mt-2 space-y-1 text-sm">
        {(jobs.data || []).map((job) => (
          <li key={job.id}>
            {job.created_at.slice(0, 19)} · {job.kind} · {job.status} · {JSON.stringify(job.stats)}
          </li>
        ))}
      </ul>
    </div>
  );
}
