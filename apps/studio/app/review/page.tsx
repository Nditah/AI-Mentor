"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { api } from "@/lib/api";

type Asset = { id: string; title: string; topic: string; author_name: string };

export default function ReviewPage() {
  const query = useQuery({
    queryKey: ["review"],
    queryFn: () => api<Asset[]>("/api/v1/content/assets?state=review"),
  });
  return (
    <div>
      <h1 className="text-3xl font-semibold tracking-tight">Review queue</h1>
      <p className="mt-2 max-w-2xl text-slate-600 dark:text-slate-300">
        An instructor cannot approve a resource they submitted. An admin can, and the audit log marks that as self-approved.
      </p>
      {query.data?.length === 0 ? <p className="mt-6">Nothing is waiting for review.</p> : null}
      <ul className="mt-6 space-y-3">
        {(query.data || []).map((asset) => (
          <li key={asset.id}>
            <Link className="font-semibold underline" href={`/library/${asset.id}`}>
              {asset.title}
            </Link>
            <p className="text-sm text-slate-600 dark:text-slate-300">
              {asset.topic || "No topic"} · {asset.author_name}
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}
