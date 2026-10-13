"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { use } from "react";
import { MentorMarkdown } from "@/components/markdown-view";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { PathDetail } from "@/lib/types";
import { useStudio } from "@/stores/studio";

export default function PathDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = use(params);
  const devUserId = useStudio((state) => state.devUserId);
  const client = useQueryClient();
  const query = useQuery({
    queryKey: ["path", slug, devUserId],
    queryFn: () => api<PathDetail>(`/api/v1/learning-paths/${slug}`),
  });
  const complete = useMutation({
    mutationFn: (lesson: string) => api(`/api/v1/progress/lessons/${lesson}/complete`, { method: "POST" }),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["path", slug] });
      client.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
  if (query.isLoading) return <p>Loading the path…</p>;
  if (!query.data) return <p>That path was not found.</p>;
  const path = query.data;
  return (
    <article>
      <p className="text-sm font-semibold uppercase tracking-wide text-[#1d4ed8]">{path.level}</p>
      <h1 className="font-display text-4xl tracking-tight">{path.title}</h1>
      <p className="mt-2 max-w-3xl text-slate-700 dark:text-slate-300">{path.description}</p>
      <ol className="mt-8 space-y-6">
        {path.steps.map((step) => (
          <li key={step.slug || step.position} className="rounded-3xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-2xl font-semibold">{step.title}</h2>
              <p className="text-sm">{step.completed ? "Completed" : "Not completed"}</p>
            </div>
            {step.prerequisites.length ? (
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
                Prerequisites: {step.prerequisites.join(", ")}
              </p>
            ) : (
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">No prerequisites.</p>
            )}
            {step.content_md ? <MentorMarkdown content={step.content_md} /> : null}
            {step.slug && !step.completed ? (
              <Button type="button" onClick={() => complete.mutate(step.slug!)} disabled={complete.isPending}>
                Mark lesson complete
              </Button>
            ) : null}
          </li>
        ))}
      </ol>
    </article>
  );
}
