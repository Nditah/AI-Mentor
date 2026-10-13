"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { api } from "@/lib/api";

type Challenge = {
  id: string;
  title: string;
  topic: string;
  difficulty: string;
  resource_type_label: string;
  challenge?: {
    language: string;
    variant: string;
    entrypoint: string;
    hidden_test_count: number;
    has_reference: boolean;
  };
};

export default function ChallengesPage() {
  const query = useQuery({
    queryKey: ["studio-challenges"],
    queryFn: () => api<{ items: Challenge[] }>("/api/v1/content/challenges?limit=200"),
  });
  const items = query.data?.items || [];
  return (
    <div>
      <h1 className="text-3xl font-semibold tracking-tight">Challenge definitions</h1>
      <p className="mt-2 max-w-2xl text-slate-600 dark:text-slate-300">
        Authored specs for the coding lab. Hidden tests and reference solutions stay on the server.
        Scheduling a challenge for a date is a gamification concern, not this screen.
      </p>
      {query.isLoading ? <p className="mt-6">Loading challenges…</p> : null}
      {query.data && items.length === 0 ? (
        <p className="mt-6">No challenge specs yet. Seed the Knowledge Pack.</p>
      ) : null}
      <ul className="mt-6 space-y-2">
        {items.map((item) => (
          <li key={item.id} className="rounded-2xl border border-slate-200 p-4 dark:border-slate-700">
            <Link className="font-semibold underline" href={`/catalog/${item.id}`}>
              {item.title}
            </Link>
            <p className="text-sm text-slate-600 dark:text-slate-300">
              {item.topic} · {item.difficulty}
              {item.challenge
                ? ` · ${item.challenge.language} ${item.challenge.variant} · ${item.challenge.hidden_test_count} hidden tests`
                : ""}
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}
