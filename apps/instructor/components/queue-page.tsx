"use client";

export function QueuePage({
  title,
  description,
  empty,
}: {
  title: string;
  description: string;
  empty: string;
}) {
  return (
    <div>
      <h1 className="text-3xl font-semibold tracking-tight">{title}</h1>
      <p className="mt-2 max-w-2xl text-slate-600 dark:text-slate-300">{description}</p>
      <p className="mt-8 rounded-2xl border border-dashed border-slate-300 bg-white p-6 text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300">
        {empty}
      </p>
    </div>
  );
}
