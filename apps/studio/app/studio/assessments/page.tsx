"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

type Item = { title: string; resource_type_label: string; topic: string; difficulty: string };

export default function AssessmentsPage() {
  const query = useQuery({
    queryKey: ["challenges-catalog"],
    queryFn: () => api<{ items: Item[] }>("/api/v1/resources?resource_type=coding_challenge&limit=40"),
  });
  return (
    <div>
      <h1 className="text-3xl font-semibold tracking-tight">Assessment generator</h1>
      <p className="mt-2 max-w-2xl text-slate-600 dark:text-slate-300">
        Question-bank items and coding challenges ship in Knowledge Pack v1.0. Answer keys never leave the API.
        Generate a learner quiz from the existing quiz endpoint; it copies a key server-side.
      </p>
      <h2 className="mt-8 text-xl font-semibold">Published coding challenges</h2>
      <ul className="mt-3 space-y-2 text-sm">
        {(query.data?.items || []).map((item) => (
          <li key={item.title} className="rounded-2xl border border-slate-200 p-3 dark:border-slate-700">
            <span className="font-semibold">{item.title}</span>
            <span className="block text-slate-600 dark:text-slate-300">
              {item.topic} · {item.difficulty}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
