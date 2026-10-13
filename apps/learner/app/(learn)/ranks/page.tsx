"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { Button } from "@/components/ui/button";
import { api, ApiError } from "@/lib/api";
import { useStudio } from "@/stores/studio";

type Entry = {
  rank: number;
  display_name: string;
  xp: number;
  level: number;
  streak_days: number;
  title: string | null;
  badges: number;
};
type Board = {
  scope: string;
  country: string | null;
  entries: Entry[];
  me: { rank: number; xp: number; level: number } | null;
};

export default function RanksPage() {
  const client = useQueryClient();
  const devUserId = useStudio((state) => state.devUserId);
  const [scope, setScope] = useState<"global" | "country">("global");
  const [country, setCountry] = useState("GB");
  const query = useQuery({
    queryKey: ["leaderboards", scope, devUserId],
    queryFn: () => api<Board>(`/api/v1/leaderboards?scope=${scope}`),
    retry: false,
  });
  const saveCountry = useMutation({
    mutationFn: () =>
      api("/api/v1/me", {
        method: "PATCH",
        body: JSON.stringify({ country_code: country.toUpperCase() }),
      }),
    onSuccess: () => client.invalidateQueries({ queryKey: ["leaderboards"] }),
  });

  function onCountry(event: FormEvent) {
    event.preventDefault();
    saveCountry.mutate();
  }

  const missingCountry = query.error instanceof ApiError && query.error.status === 409;

  return (
    <div className="max-w-3xl">
      <h1 className="font-display text-4xl tracking-tight">Ranks</h1>
      <p className="mt-2 text-slate-700 dark:text-slate-300">
        Pseudonymous standings by XP. Institution, cohort, and friends boards ship with classrooms. Rank never drops with a nag.
      </p>
      <div className="mt-4 flex gap-2">
        {(["global", "country"] as const).map((item) => (
          <Button key={item} type="button" variant={scope === item ? "primary" : "quiet"} onClick={() => setScope(item)}>
            {item === "global" ? "Global" : "Country"}
          </Button>
        ))}
      </div>
      {missingCountry ? (
        <form className="mt-6 rounded-3xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900" onSubmit={onCountry}>
          <p className="font-semibold">Set a country on your profile to open that board.</p>
          <label className="mt-3 block text-sm font-semibold">
            ISO country code
            <input
              className="mt-1 block rounded-full border border-slate-300 bg-white px-3 py-2 uppercase dark:border-slate-600 dark:bg-slate-950"
              value={country}
              maxLength={2}
              onChange={(event) => setCountry(event.target.value)}
            />
          </label>
          <Button className="mt-3" type="submit" disabled={saveCountry.isPending}>
            Save country
          </Button>
        </form>
      ) : null}
      {query.isLoading ? <p className="mt-6">Loading standings…</p> : null}
      {query.error && !missingCountry ? <p className="mt-6">Standings are unavailable.</p> : null}
      {query.data ? (
        <>
          {query.data.me ? (
            <p className="mt-6 text-sm font-semibold">
              Your place: #{query.data.me.rank} · {query.data.me.xp} XP · level {query.data.me.level}
              {query.data.country ? ` · ${query.data.country}` : ""}
            </p>
          ) : null}
          <ol className="mt-4 space-y-2">
            {query.data.entries.map((entry) => (
              <li
                key={`${entry.rank}-${entry.display_name}`}
                className="flex flex-wrap items-baseline justify-between gap-2 rounded-3xl border border-slate-200 bg-white px-4 py-3 dark:border-slate-700 dark:bg-slate-900"
              >
                <span className="font-semibold">
                  #{entry.rank} {entry.display_name}
                  {entry.title ? ` · ${entry.title}` : ""}
                </span>
                <span className="text-sm text-slate-600 dark:text-slate-300">
                  {entry.xp} XP · L{entry.level} · {entry.streak_days}d · {entry.badges} badges
                </span>
              </li>
            ))}
          </ol>
        </>
      ) : null}
    </div>
  );
}
