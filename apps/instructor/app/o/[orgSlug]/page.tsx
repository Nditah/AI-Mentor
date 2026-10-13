"use client";

import { use } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";

type Overview = {
  users: number;
  students: number;
  published: number;
  review_queue: number;
  quizzes_taken: number;
  note: string;
};

export default function InstructorHome({ params }: { params: Promise<{ orgSlug: string }> }) {
  const { orgSlug } = use(params);
  const query = useQuery({
    queryKey: ["overview", orgSlug],
    queryFn: () => api<Overview>("/api/v1/admin/overview"),
    retry: false,
  });
  if (query.error instanceof ApiError) return <p>{query.error.message}</p>;
  if (!query.data) return <p>Loading your teaching home…</p>;
  const data = query.data;
  const base = `/o/${orgSlug}`;
  return (
    <div>
      <h1 className="text-3xl font-semibold tracking-tight">Teaching home</h1>
      <p className="mt-2 max-w-2xl text-slate-600 dark:text-slate-300">
        Queues for {orgSlug}. Instructors consume published path releases; they do not edit the master
        catalog. That work lives in Content Studio.
      </p>
      <dl className="mt-6 grid gap-3 sm:grid-cols-3">
        {[
          ["Learners (platform)", data.students],
          ["Published resources", data.published],
          ["Quizzes taken", data.quizzes_taken],
        ].map(([label, value]) => (
          <div key={String(label)} className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
            <dt className="text-sm text-slate-600 dark:text-slate-300">{label}</dt>
            <dd className="text-3xl font-semibold">{value}</dd>
          </div>
        ))}
      </dl>
      <ul className="mt-8 space-y-2">
        <li><Link className="underline" href={`${base}/cohorts`}>Open cohorts</Link></li>
        <li><Link className="underline" href={`${base}/marking`}>Marking queue</Link></li>
        <li><Link className="underline" href={`${base}/learners`}>All learners</Link></li>
      </ul>
    </div>
  );
}
