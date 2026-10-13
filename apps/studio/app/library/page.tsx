"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { api } from "@/lib/api";

type Asset = {
  id: string;
  title: string;
  kind: string;
  state: string;
  difficulty: string;
  topic: string;
  language: string;
  version: number;
};

export default function LibraryPage() {
  const query = useQuery({
    queryKey: ["assets"],
    queryFn: () => api<Asset[]>("/api/v1/admin/assets"),
  });
  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-3xl font-semibold tracking-tight">Library</h1>
        <Link className="rounded-full bg-[#1d4ed8] px-4 py-2 text-sm font-semibold text-white" href="/library/new">
          Add resource
        </Link>
      </div>
      <p className="mt-2 max-w-2xl text-slate-600 dark:text-slate-300">
        Drafts stay private. Students see a resource only after an admin publishes it.
      </p>
      {query.isLoading ? <p className="mt-6">Loading the library…</p> : null}
      {query.data && query.data.length === 0 ? (
        <p className="mt-6">Add your first resource. Markdown lessons and catalog drafts are supported.</p>
      ) : null}
      {query.data && query.data.length > 0 ? (
        <div className="mt-6 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <caption className="sr-only">Knowledge library</caption>
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-700">
                <th className="py-2">Title</th>
                <th>Type</th>
                <th>Topic</th>
                <th>State</th>
                <th>Difficulty</th>
              </tr>
            </thead>
            <tbody>
              {query.data.map((asset) => (
                <tr key={asset.id} className="border-b border-slate-100 dark:border-slate-800">
                  <td className="py-2">
                    <Link className="font-semibold underline" href={`/library/${asset.id}`}>
                      {asset.title}
                    </Link>
                    <span className="block text-slate-500">v{asset.version} · {asset.language}</span>
                  </td>
                  <td>{asset.kind}</td>
                  <td>{asset.topic || "—"}</td>
                  <td>{asset.state}</td>
                  <td>{asset.difficulty}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}
