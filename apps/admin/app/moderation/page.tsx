"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export default function ModerationPage() {
  const query = useQuery({
    queryKey: ["moderation"],
    queryFn: () => api<{ items: unknown[]; note: string }>("/api/v1/admin/moderation"),
  });
  return (
    <div>
      <h1 className="text-3xl font-semibold tracking-tight">Moderation</h1>
      <p className="mt-2 max-w-2xl text-slate-600 dark:text-slate-300">{query.data?.note || "Loading the queue…"}</p>
    </div>
  );
}
