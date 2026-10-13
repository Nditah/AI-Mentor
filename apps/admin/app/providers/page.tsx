"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

type Providers = {
  openai: boolean;
  anthropic: boolean;
  gemini: boolean;
  qdrant: boolean;
  note: string;
};

export default function ProvidersPage() {
  const query = useQuery({
    queryKey: ["providers"],
    queryFn: () => api<Providers>("/api/v1/admin/providers"),
    retry: false,
  });
  const data = query.data;
  return (
    <div>
      <h1 className="text-3xl font-semibold tracking-tight">AI providers</h1>
      {data ? <p className="mt-2 max-w-2xl text-slate-600 dark:text-slate-300">{data.note}</p> : null}
      <ul className="mt-6 space-y-2">
        {data
          ? [
              ["OpenAI", data.openai],
              ["Anthropic", data.anthropic],
              ["Gemini", data.gemini],
              ["Qdrant", data.qdrant],
            ].map(([name, on]) => (
              <li key={String(name)} className="rounded-2xl border border-slate-200 bg-white px-4 py-3 dark:border-slate-700 dark:bg-slate-900">
                <span className="font-semibold">{name}</span>
                <span className="ml-2 text-sm">{on ? "Configured" : "Not configured"}</span>
              </li>
            ))
          : null}
      </ul>
    </div>
  );
}
