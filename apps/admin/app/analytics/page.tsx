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

type Learning = {
  most_completed_lessons: { title: string; completions: number }[];
  highest_drop_off_pages: { page: string; lesson: string; drop_off: number; seen: number }[];
  assessment_pass_rates: { title: string; scope: string; attempts: number; pass_rate: number }[];
  course_completion: { title: string; attempts: number; pass_rate: number }[];
  path_completion: { title: string; attempts: number; pass_rate: number }[];
  time_on_lesson: { title: string; minutes: number }[];
};

export default function AnalyticsPage() {
  const query = useQuery({
    queryKey: ["analytics"],
    queryFn: () => api<Analytics>("/api/v1/admin/analytics"),
  });
  const learning = useQuery({
    queryKey: ["learning-metrics"],
    queryFn: () => api<Learning>("/api/v1/admin/learning"),
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
      <h2 className="mt-10 text-xl font-semibold">Guided learning</h2>
      {learning.data ? <LearningTables data={learning.data} /> : <p className="mt-3">Loading learning metrics…</p>}
    </div>
  );
}

function LearningTables({ data }: { data: Learning }) {
  const blocks: [string, string[]][] = [
    ["Most completed lessons", data.most_completed_lessons.map((item) => `${item.title} · ${item.completions}`)],
    ["Highest drop-off pages", data.highest_drop_off_pages.map((item) => `${item.lesson} / ${item.page} · ${item.drop_off}% of ${item.seen}`)],
    ["Assessment pass rates", data.assessment_pass_rates.map((item) => `${item.scope} · ${item.title} · ${item.pass_rate}% of ${item.attempts}`)],
    ["Course completion", data.course_completion.map((item) => `${item.title} · ${item.pass_rate}% of ${item.attempts}`)],
    ["Learning path completion", data.path_completion.map((item) => `${item.title} · ${item.pass_rate}% of ${item.attempts}`)],
    ["Time on lesson", data.time_on_lesson.map((item) => `${item.title} · ${item.minutes} min`)],
  ];
  return (
    <div className="mt-4 grid gap-4 lg:grid-cols-2">
      {blocks.map(([title, rows]) => (
        <section key={title} className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
          <h3 className="font-semibold">{title}</h3>
          {rows.length ? (
            <ul className="mt-2 space-y-1 text-sm">
              {rows.map((row) => <li key={row}>{row}</li>)}
            </ul>
          ) : (
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">No rows yet.</p>
          )}
        </section>
      ))}
    </div>
  );
}
