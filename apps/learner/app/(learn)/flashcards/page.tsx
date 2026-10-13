"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { useStudio } from "@/stores/studio";

type Card = { id: string; front: string; back: string; concept_slug: string | null };

const ratings = [
  ["Again", 1],
  ["Hard", 3],
  ["Good", 4],
  ["Easy", 5],
] as const;

export default function FlashcardsPage() {
  const devUserId = useStudio((state) => state.devUserId);
  const client = useQueryClient();
  const [showBack, setShowBack] = useState(false);
  const [concept, setConcept] = useState("q-learning");
  const due = useQuery({
    queryKey: ["cards", devUserId],
    queryFn: () => api<Card[]>("/api/v1/flashcards/due"),
  });
  const generate = useMutation({
    mutationFn: () => api("/api/v1/flashcards/generate", { method: "POST", body: JSON.stringify({ concept_slug: concept }) }),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["cards"] });
      client.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
  const review = useMutation({
    mutationFn: (rating: number) =>
      api(`/api/v1/flashcards/${due.data?.[0].id}/review`, {
        method: "POST",
        body: JSON.stringify({ rating }),
      }),
    onSuccess: () => {
      setShowBack(false);
      client.invalidateQueries({ queryKey: ["cards"] });
      client.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
  const card = due.data?.[0];
  return (
    <div className="max-w-2xl">
      <h1 className="font-display text-4xl tracking-tight">Flashcards</h1>
      <p className="mt-2 text-slate-700 dark:text-slate-300">Reviews use SM-2. Again, Hard, Good, and Easy map to qualities 1, 3, 4, and 5.</p>
      <form
        className="mt-4 flex flex-wrap items-end gap-3"
        onSubmit={(event) => {
          event.preventDefault();
          generate.mutate();
        }}
      >
        <label className="text-sm font-semibold">
          Concept slug
          <input
            className="mt-1 block rounded-full border border-slate-300 bg-white px-3 py-2 dark:border-slate-600 dark:bg-slate-950"
            value={concept}
            onChange={(event) => setConcept(event.target.value)}
          />
        </label>
        <Button type="submit">Make a deck</Button>
      </form>
      {due.isLoading ? <p className="mt-6">Loading cards…</p> : null}
      {!due.isLoading && !card ? <p className="mt-6">Nothing is due. Generate a deck or come back when the interval elapses.</p> : null}
      {card ? (
        <article className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{showBack ? "Back" : "Front"}</p>
          <p className="mt-3 text-xl">{showBack ? card.back : card.front}</p>
          {showBack ? (
            <div className="mt-6 flex flex-wrap gap-2">
              {ratings.map(([label, rating]) => (
                <Button key={label} type="button" variant="quiet" onClick={() => review.mutate(rating)}>
                  {label}
                </Button>
              ))}
            </div>
          ) : (
            <Button className="mt-6" type="button" onClick={() => setShowBack(true)}>
              Show answer
            </Button>
          )}
        </article>
      ) : null}
    </div>
  );
}
