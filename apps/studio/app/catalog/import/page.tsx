"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { api, ApiError } from "@/lib/api";

type Source = { slug: string; name: string; provider: string; status: string; last_error: string; terms_note: string };
type Job = { id: string; kind: string; status: string; stats: Record<string, number>; created_at: string };

function parseCsv(text: string): Record<string, unknown>[] {
  const lines = text.replace(/^\uFEFF/, "").split(/\r?\n/).filter((line) => line.trim().length > 0);
  if (lines.length < 2) return [];
  const headers = splitCsvLine(lines[0]);
  return lines.slice(1).map((line) => {
    const cells = splitCsvLine(line);
    const row: Record<string, unknown> = {};
    headers.forEach((header, index) => {
      const key = header.trim();
      const value = (cells[index] || "").trim();
      if (!key) return;
      if (key === "concepts") {
        row[key] = value.split(/[,;|]/).map((part) => part.trim()).filter(Boolean);
      } else if (key === "estimated_duration" && value) {
        const n = Number(value);
        row[key] = Number.isFinite(n) ? n : value;
      } else {
        row[key] = value;
      }
    });
    return row;
  });
}

function splitCsvLine(line: string): string[] {
  const cells: string[] = [];
  let current = "";
  let quoted = false;
  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];
    if (char === '"') {
      if (quoted && line[i + 1] === '"') {
        current += '"';
        i += 1;
      } else {
        quoted = !quoted;
      }
    } else if (char === "," && !quoted) {
      cells.push(current);
      current = "";
    } else {
      current += char;
    }
  }
  cells.push(current);
  return cells;
}

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
      setNote("Choose a JSON or CSV file first.");
      return;
    }
    const text = await file.text();
    const csv = file.name.toLowerCase().endsWith(".csv") || file.type === "text/csv";
    let resources: unknown[] | undefined;
    if (csv) {
      try {
        resources = parseCsv(text);
      } catch {
        setNote("The CSV could not be read. Use a header row and UTF-8 text.");
        return;
      }
    } else {
      try {
        const parsed = JSON.parse(text) as unknown;
        resources = Array.isArray(parsed) ? parsed : (parsed as { resources?: unknown[] }).resources;
      } catch {
        setNote("The JSON file is not valid.");
        return;
      }
    }
    if (!Array.isArray(resources) || resources.length === 0) {
      setNote("The file must contain at least one resource.");
      return;
    }
    upload.mutate(resources);
  }

  return (
    <div className="max-w-3xl">
      <h1 className="text-3xl font-semibold tracking-tight">Asset import centre</h1>
      <p className="mt-2 text-slate-600 dark:text-slate-300">
        Bulk JSON or CSV goes through the twelve-stage ingestion pipeline. CSV needs a header row matching the JSON fields (title, url, resource_type, …). Remote harvests stay paused until a connector token is set.
      </p>
      <form className="mt-6 space-y-3" onSubmit={onFile}>
        <label className="block text-sm font-semibold">
          JSON or CSV file
          <input className="mt-1 block" name="file" type="file" accept=".json,.csv,application/json,text/csv" />
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
