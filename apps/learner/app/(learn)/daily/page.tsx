"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { Button } from "@/components/ui/button";
import { api, ApiError } from "@/lib/api";
import { useStudio } from "@/stores/studio";

type Daily = {
  date: string;
  xp_reward: number;
  completed: boolean;
  kind: string;
  prompt: string;
  options: string[];
  concept_slug: string;
  question_id: string;
};

type DailyResult = { correct: boolean; xp: number; completed: boolean };

export default function DailyPage() {
  const client = useQueryClient();
  const devUserId = useStudio((state) => state.devUserId);
  const [response, setResponse] = useState("");
  const query = useQuery({
    queryKey: ["daily", devUserId],
    queryFn: () => api<Daily>("/api/v1/engagement/daily"),
  });
  const submit = useMutation({
    mutationFn: () =>
      api<DailyResult>("/api/v1/engagement/daily", {
        method: "POST",
        body: JSON.stringify({ response }),
      }),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["daily"] });
      client.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    submit.mutate();
  }

  if (query.isLoading) return <p>Loading today’s challenge…</p>;
  if (query.error) {
    const message = query.error instanceof ApiError ? query.error.message : "The daily challenge is unavailable.";
    return <p>{message}</p>;
  }
  const daily = query.data!;
  const result = submit.data;

  return (
    <div className="max-w-3xl">
      <h1 className="font-display text-4xl tracking-tight">Today</h1>
      <p className="mt-2 text-slate-700 dark:text-slate-300">
        One authored item for {daily.date}. A correct answer pays {daily.xp_reward} XP once, inside the 400 XP daily cap.
        Missing a day does not take yesterday’s streak away if a freeze is ready.
      </p>
      <article className="mt-6 rounded-3xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900">
        <p className="text-xs font-semibold uppercase tracking-wide text-[#b91c1c]">Daily challenge</p>
        <p className="mt-2 text-lg font-semibold">{daily.prompt}</p>
        {daily.completed ? (
          <p className="mt-4 font-semibold text-emerald-700 dark:text-emerald-300">Completed for today.</p>
        ) : (
          <form className="mt-4 space-y-3" onSubmit={onSubmit}>
            {daily.options.length ? (
              <fieldset>
                <legend className="sr-only">Choose an answer</legend>
                <ul className="space-y-2">
                  {daily.options.map((option) => (
                    <li key={option}>
                      <label className="flex items-start gap-2 text-sm">
                        <input
                          type="radio"
                          name="daily"
                          value={option}
                          checked={response === option}
                          onChange={() => setResponse(option)}
                        />
                        <span>{option}</span>
                      </label>
                    </li>
                  ))}
                </ul>
              </fieldset>
            ) : (
              <label className="block text-sm font-semibold">
                Your answer
                <textarea
                  className="mt-1 block w-full rounded-2xl border border-slate-300 bg-white px-3 py-2 dark:border-slate-600 dark:bg-slate-950"
                  rows={4}
                  value={response}
                  onChange={(event) => setResponse(event.target.value)}
                />
              </label>
            )}
            <Button type="submit" disabled={!response || submit.isPending}>
              {submit.isPending ? "Checking…" : "Submit"}
            </Button>
          </form>
        )}
        {result ? (
          <p className={`mt-4 text-sm font-semibold ${result.correct ? "xp-pop text-emerald-700 dark:text-emerald-300" : "text-[#b91c1c]"}`}>
            {result.correct
              ? result.xp
                ? `Correct. +${result.xp} XP.`
                : "Correct. Already counted for today."
              : "Not quite. Try again — the streak is safe."}
          </p>
        ) : null}
      </article>
    </div>
  );
}
