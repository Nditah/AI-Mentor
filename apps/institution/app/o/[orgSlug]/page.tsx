"use client";

import { use } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";

type Overview = {
  users: number;
  students: number;
  published: number;
  note: string;
};

export default function InstitutionHome({ params }: { params: Promise<{ orgSlug: string }> }) {
  const { orgSlug } = use(params);
  const query = useQuery({
    queryKey: ["overview", orgSlug],
    queryFn: () => api<Overview>("/api/v1/admin/overview"),
    retry: false,
  });
  if (query.error instanceof ApiError) return <p>{query.error.message}</p>;
  if (!query.data) return <p>Loading the organisation…</p>;
  const data = query.data;
  const base = `/o/${orgSlug}`;
  return (
    <div>
      <h1 className="text-3xl font-semibold tracking-tight">Organisation overview</h1>
      <p className="mt-2 max-w-2xl text-slate-600 dark:text-slate-300">
        {orgSlug} on the shared platform. Licences, people, and compliance live here. Teaching lives in
        the Instructor App. Master content lives in Content Studio.
      </p>
      <dl className="mt-6 grid gap-3 sm:grid-cols-3">
        {[
          ["People (platform)", data.users],
          ["Learners", data.students],
          ["Published resources", data.published],
        ].map(([label, value]) => (
          <div key={String(label)} className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
            <dt className="text-sm text-slate-600 dark:text-slate-300">{label}</dt>
            <dd className="text-3xl font-semibold">{value}</dd>
          </div>
        ))}
      </dl>
      <ul className="mt-8 space-y-2">
        <li><Link className="underline" href={`${base}/people`}>People</Link></li>
        <li><Link className="underline" href={`${base}/licences`}>Licences</Link></li>
        <li><Link className="underline" href={`${base}/compliance`}>Compliance</Link></li>
      </ul>
    </div>
  );
}
