"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

type Config = { editable: boolean; note: string; values: { key: string; value: number; allowed: string }[] };

export default function ConfigurationPage() {
  const query = useQuery({
    queryKey: ["config"],
    queryFn: () => api<Config>("/api/v1/admin/configuration"),
    retry: false,
  });
  return (
    <div>
      <h1 className="text-3xl font-semibold tracking-tight">Configuration</h1>
      {query.data ? <p className="mt-2 max-w-2xl text-slate-600 dark:text-slate-300">{query.data.note}</p> : null}
      <table className="mt-6 w-full max-w-xl text-left text-sm">
        <caption className="sr-only">Compiled mentor settings</caption>
        <thead>
          <tr className="border-b border-slate-200 dark:border-slate-700">
            <th className="py-2">Setting</th>
            <th>Value</th>
            <th>Allowed</th>
          </tr>
        </thead>
        <tbody>
          {(query.data?.values || []).map((row) => (
            <tr key={row.key} className="border-b border-slate-100 dark:border-slate-800">
              <td className="py-2">{row.key}</td>
              <td>{row.value}</td>
              <td>{row.allowed}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
