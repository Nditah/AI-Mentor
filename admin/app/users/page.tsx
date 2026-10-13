"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";

type UserRow = {
  id: string;
  display_name: string;
  email: string;
  role: string;
  xp: number;
  streak_days: number;
};

export default function UsersPage() {
  const client = useQueryClient();
  const [queryText, setQueryText] = useState("");
  const [reason, setReason] = useState("");
  const users = useQuery({
    queryKey: ["users"],
    queryFn: () => api<UserRow[]>("/api/v1/admin/users"),
    retry: false,
  });
  const save = useMutation({
    mutationFn: (input: { id: string; role: string }) =>
      api(`/api/v1/admin/users/${input.id}`, {
        method: "PATCH",
        body: JSON.stringify({ role: input.role, reason }),
      }),
    onSuccess: () => client.invalidateQueries({ queryKey: ["users"] }),
  });
  const needle = queryText.trim().toLowerCase();
  const rows = (users.data || []).filter((user) =>
    `${user.display_name} ${user.email} ${user.id}`.toLowerCase().includes(needle),
  );
  return (
    <div>
      <h1 className="text-3xl font-semibold tracking-tight">Users</h1>
      <p className="mt-2 max-w-2xl text-slate-600 dark:text-slate-300">
        Role changes require a reason and are written to the audit log. The last admin cannot be demoted.
      </p>
      <label className="mt-4 block max-w-md text-sm font-semibold">
        Search name, email, or id
        <input className="mt-1 w-full rounded-full border border-slate-300 bg-white px-3 py-2 dark:border-slate-600 dark:bg-slate-950" value={queryText} onChange={(event) => setQueryText(event.target.value)} />
      </label>
      <label className="mt-3 block max-w-md text-sm font-semibold">
        Reason for the next role change
        <input className="mt-1 w-full rounded-full border border-slate-300 bg-white px-3 py-2 dark:border-slate-600 dark:bg-slate-950" value={reason} onChange={(event) => setReason(event.target.value)} />
      </label>
      {users.error ? <p className="mt-4">{users.error.message}</p> : null}
      <div className="mt-6 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <caption className="sr-only">Accounts</caption>
          <thead>
            <tr className="border-b border-slate-200 dark:border-slate-700">
              <th className="py-2">Name</th>
              <th>Role</th>
              <th>XP</th>
              <th>Streak</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((user) => (
              <tr key={user.id} className="border-b border-slate-100 dark:border-slate-800">
                <td className="py-2">
                  {user.display_name}
                  <span className="block text-slate-500">{user.email}</span>
                </td>
                <td>
                  <label className="sr-only" htmlFor={`role-${user.id}`}>
                    Role for {user.display_name}
                  </label>
                  <select
                    id={`role-${user.id}`}
                    className="rounded-full border border-slate-300 bg-white px-2 py-1 dark:border-slate-600 dark:bg-slate-950"
                    value={user.role}
                    onChange={(event) => save.mutate({ id: user.id, role: event.target.value })}
                  >
                    <option value="student">student</option>
                    <option value="instructor">instructor</option>
                    <option value="admin">admin</option>
                  </select>
                </td>
                <td>{user.xp}</td>
                <td>{user.streak_days}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {save.error ? <p className="mt-3 text-red-800 dark:text-red-300">{save.error.message}</p> : null}
    </div>
  );
}
