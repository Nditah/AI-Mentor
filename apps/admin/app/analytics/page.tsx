"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

type Analytics = {
  users: number;
  students: number;
  conversations: number;
  quizzes_taken: number;
  documents: number;
  average_mastery: number;
};

export default function AnalyticsPage() {
  const query = useQuery({
    queryKey: ["analytics"],
    queryFn: () => api<Analytics>("/api/v1/admin/analytics"),
  });
  const data = query.data;
  return (
    <div>
      <h1 className="text-3xl font-semibold tracking-tight">Analytics</h1>
      <p className="mt-2 max-w-2xl text-slate-600 dark:text-slate-300">
        These figures are counted from the database. Segments under 20 learners are not hidden yet, because the studio is still small. Visit, retention, and cost charts are not collected.
      </p>
      {data ? (
        <dl className="mt-6 grid gap-3 sm:grid-cols-3">
          {[
            ["Learners", data.users],
            ["Students", data.students],
            ["Quizzes", data.quizzes_taken],
            ["Documents", data.documents],
            ["Conversations", data.conversations],
            ["Average mastery", Math.round(data.average_mastery)],
          ].map(([label, value]) => (
            <div key={String(label)} className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
              <dt className="text-sm text-slate-600 dark:text-slate-300">{label}</dt>
              <dd className="text-3xl font-semibold">{value}</dd>
            </div>
          ))}
        </dl>
      ) : (
        <p className="mt-6">Loading analytics…</p>
      )}
    </div>
  );
}
