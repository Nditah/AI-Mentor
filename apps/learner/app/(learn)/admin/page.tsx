export default function AdminPage() {
  return (
    <div>
      <h1 className="font-display text-4xl tracking-tight">Admin</h1>
      <p className="mt-2 max-w-xl text-slate-700 dark:text-slate-300">
        Library, review, curriculum, analytics, and user management live in the admin portal, a separate app for instructors and admins.
      </p>
      <a className="mt-4 inline-block font-semibold text-[#1d4ed8] underline" href={process.env.NEXT_PUBLIC_ADMIN_URL || "http://localhost:3001"}>
        Open the admin portal
      </a>
    </div>
  );
}
