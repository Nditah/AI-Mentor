"use client";

import { useQuery } from "@tanstack/react-query";
import { api, ApiError, studioUrl } from "@/lib/api";

type Overview = {
  users: number;
  students: number;
  conversations: number;
  quizzes_taken: number;
  documents: number;
  published: number;
  review_queue: number;
  note: string;
};

export default function OverviewPage() {
  const query = useQuery({
    queryKey: ["overview"],
    queryFn: () => api<Overview>("/api/v1/admin/overview"),
    retry: false,
  });
  if (query.error instanceof ApiError) return <p>{query.error.message}</p>;
  if (!query.data) return <p>Loading the portal…</p>;
  const data = query.data;
  const tiles = [
    ["Learners", data.users],
    ["Students", data.students],
    ["Published resources", data.published],
    ["In review", data.review_queue],
    ["Quizzes taken", data.quizzes_taken],
    ["Learner documents", data.documents],
    ["Conversations", data.conversations],
  ];
  return (
    <div>
      <h1 className="text-3xl font-semibold tracking-tight">Overview</h1>
      <p className="mt-2 max-w-2xl text-slate-600 dark:text-slate-300">{data.note}</p>
      <dl className="mt-6 grid gap-3 sm:grid-cols-3">
        {tiles.map(([label, value]) => (
          <div key={String(label)} className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
            <dt className="text-sm text-slate-600 dark:text-slate-300">{label}</dt>
            <dd className="text-3xl font-semibold">{value}</dd>
          </div>
        ))}
      </dl>
      <section className="mt-8">
        <h2 className="text-xl font-semibold">Needs attention</h2>
        <ul className="mt-2 space-y-1">
          <li>
            <a className="underline" href={`${studioUrl}/review`}>
              {data.review_queue} resources in review (Content Studio)
            </a>
          </li>
        </ul>
      </section>
    </div>
  );
}
