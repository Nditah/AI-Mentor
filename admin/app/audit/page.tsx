"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

type Event = {
  id: string;
  action: string;
  entity_type: string;
  actor: string;
  created_at: string;
  detail: { self_approved?: boolean; reason?: string; state?: string; note?: string };
};

export default function AuditPage() {
  const query = useQuery({
    queryKey: ["audit"],
    queryFn: () => api<Event[]>("/api/v1/admin/audit"),
    retry: false,
  });
  return (
    <div>
      <h1 className="text-3xl font-semibold tracking-tight">Audit log</h1>
      <ul className="mt-6 space-y-3">
        {(query.data || []).map((event) => (
          <li key={event.id} className="rounded-2xl border border-slate-200 bg-white p-4 text-sm dark:border-slate-700 dark:bg-slate-900">
            <p className="font-semibold">
              {event.action} · {event.entity_type}
            </p>
            <p>
              {event.actor} · {event.created_at}
            </p>
            {event.detail.self_approved ? <p>Self-approved</p> : null}
            {event.detail.reason ? <p>Reason: {event.detail.reason}</p> : null}
            {event.detail.note ? <p>Note: {event.detail.note}</p> : null}
          </li>
        ))}
      </ul>
      {query.data?.length === 0 ? <p className="mt-4">No admin actions have been recorded.</p> : null}
    </div>
  );
}
