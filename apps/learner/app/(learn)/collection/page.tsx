"use client";

import { useQuery } from "@tanstack/react-query";
import { SkillCardView } from "@/components/engagement";
import { api } from "@/lib/api";
import { useStudio } from "@/stores/studio";

type Card = {
  slug: string;
  name: string;
  description: string;
  mastery: number;
  difficulty: string;
  connections: string[];
  tier: string;
  skill_value: number;
};

export default function CollectionPage() {
  const devUserId = useStudio((state) => state.devUserId);
  const query = useQuery({
    queryKey: ["collection", devUserId],
    queryFn: () => api<{ count: number; cards: Card[]; note: string }>("/api/v1/engagement/collection"),
  });
  return (
    <div>
      <h1 className="font-display text-4xl tracking-tight">Collection</h1>
      <p className="mt-2 max-w-2xl text-slate-700 dark:text-slate-300">
        Skill cards appear when mastery reaches 60 (bronze), 75 (silver), or 90 (gold). They are not loot.
      </p>
      {query.isLoading ? <p className="mt-6">Loading your cards…</p> : null}
      {query.error ? <p className="mt-6">The collection is unavailable.</p> : null}
      {query.data ? (
        <>
          <p className="mt-4 text-sm font-semibold">{query.data.count} cards · {query.data.note}</p>
          {query.data.cards.length === 0 ? (
            <p className="mt-6 text-slate-600 dark:text-slate-300">Finish a lesson and a quiz to earn the first card.</p>
          ) : (
            <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {query.data.cards.map((card) => (
                <SkillCardView
                  key={card.slug}
                  name={card.name}
                  description={
                    card.connections.length
                      ? `${card.description} Connects from ${card.connections.join(", ")}.`
                      : card.description
                  }
                  tier={card.tier}
                  mastery={card.mastery}
                  difficulty={card.difficulty}
                />
              ))}
            </div>
          )}
        </>
      ) : null}
    </div>
  );
}
