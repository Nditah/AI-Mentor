"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { api } from "@/lib/api";

type Question = {
  id: string;
  key: string;
  concept_slug: string;
  difficulty: string;
  kind: string;
  prompt: string;
  options: string[];
  bloom_level: string;
};

type Challenge = { id: string; title: string; difficulty: string; topic: string };

export default function AssessmentsPage() {
  const questions = useQuery({
    queryKey: ["studio-questions"],
    queryFn: () => api<{ items: Question[] }>("/api/v1/content/questions?limit=200"),
  });
  const challenges = useQuery({
    queryKey: ["studio-challenges"],
    queryFn: () => api<{ items: Challenge[] }>("/api/v1/content/challenges?limit=100"),
  });
  return (
    <div>
      <h1 className="text-3xl font-semibold tracking-tight">Item bank</h1>
      <p className="mt-2 max-w-2xl text-slate-600 dark:text-slate-300">
        Published question-bank items and coding challenges. Answer keys and hidden tests never
        leave the API. Generate a learner quiz from the quiz endpoint; it copies a key server-side.
      </p>
      <h2 className="mt-8 text-xl font-semibold">Questions</h2>
      {questions.isLoading ? <p className="mt-2">Loading items…</p> : null}
      {questions.data && questions.data.items.length === 0 ? (
        <p className="mt-2">No published items. Seed the Knowledge Pack.</p>
      ) : null}
      <ul className="mt-3 space-y-2 text-sm">
        {(questions.data?.items || []).map((item) => (
          <li key={item.id} className="rounded-2xl border border-slate-200 p-3 dark:border-slate-700">
            <span className="font-semibold">{item.prompt}</span>
            <span className="block text-slate-600 dark:text-slate-300">
              {item.kind} · {item.concept_slug} · {item.difficulty}
              {item.bloom_level ? ` · ${item.bloom_level}` : ""}
            </span>
            {item.options?.length ? (
              <ol className="mt-1 list-decimal pl-5">
                {item.options.map((option) => (
                  <li key={option}>{option}</li>
                ))}
              </ol>
            ) : null}
          </li>
        ))}
      </ul>
      <h2 className="mt-8 text-xl font-semibold">Coding challenges</h2>
      <ul className="mt-3 space-y-2 text-sm">
        {(challenges.data?.items || []).map((item) => (
          <li key={item.id}>
            <Link className="font-semibold underline" href={`/catalog/${item.id}`}>
              {item.title}
            </Link>
            <span className="text-slate-600 dark:text-slate-300">
              {` · ${item.topic} · ${item.difficulty}`}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
