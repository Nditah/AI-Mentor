"use client";

import { useQuery } from "@tanstack/react-query";
import { api, ApiError } from "@/lib/api";
import { useStudio } from "@/stores/studio";

type AdminUser = { id: string; display_name: string; email: string; role: string; xp: number; streak_days: number };
type Analytics = { users: number; students: number; conversations: number; quizzes_taken: number; documents: number; average_mastery: number };

export default function AdminPage() {
  const devUserId = useStudio((state) => state.devUserId);
  const users = useQuery({
    queryKey: ["admin-users", devUserId],
    queryFn: () => api<AdminUser[]>("/api/v1/admin/users"),
    retry: false,
  });
  const analytics = useQuery({
    queryKey: ["admin-analytics", devUserId],
    queryFn: () => api<Analytics>("/api/v1/admin/analytics"),
    retry: false,
  });
  const forbidden = users.error instanceof ApiError && users.error.status === 403;
  return (
    <div>
      <h1 className="font-display text-4xl tracking-tight">Admin</h1>
      <p className="mt-2 max-w-xl text-slate-700 dark:text-slate-300">
        Library, review, curriculum, and user management live in the admin portal.
      </p>
      <a className="mt-4 inline-block font-semibold text-[#1d4ed8] underline" href={process.env.NEXT_PUBLIC_ADMIN_URL || "http://localhost:3001"}>
        Open the admin portal
      </a>
      {forbidden ? (
        <p className="mt-4 max-w-xl text-slate-700 dark:text-slate-300">
          This session is not an admin. On a local studio, switch the session to Demo admin. In production the role comes from Clerk, not from the browser.
        </p>
      ) : null}
      {analytics.data ? (
        <dl className="mt-6 grid gap-3 sm:grid-cols-3">
          {[
            ["Learners", analytics.data.users],
            ["Students", analytics.data.students],
            ["Quizzes", analytics.data.quizzes_taken],
            ["Documents", analytics.data.documents],
            ["Conversations", analytics.data.conversations],
            ["Average mastery", Math.round(analytics.data.average_mastery)],
          ].map(([label, value]) => (
            <div key={String(label)} className="rounded-3xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
              <dt className="text-sm text-slate-600 dark:text-slate-300">{label}</dt>
              <dd className="font-display text-3xl">{value}</dd>
            </div>
          ))}
        </dl>
      ) : null}
      {users.data ? (
        <div className="mt-6 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <caption className="sr-only">Learners</caption>
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-700">
                <th className="py-2">Name</th>
                <th>Role</th>
                <th>XP</th>
                <th>Streak</th>
              </tr>
            </thead>
            <tbody>
              {users.data.map((user) => (
                <tr key={user.id} className="border-b border-slate-100 dark:border-slate-800">
                  <td className="py-2">
                    {user.display_name}
                    <span className="block text-slate-500">{user.email}</span>
                  </td>
                  <td>{user.role}</td>
                  <td>{user.xp}</td>
                  <td>{user.streak_days}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}
