import { catalogStats } from "@/lib/api";
import { formatCount } from "@/lib/utils";

export async function ProofBar() {
  const stats = await catalogStats();
  if (!stats || stats.published === 0) return null;
  const items = [
    [stats.published, "published resources"],
    [stats.questions, "question items"],
    [stats.challenges, "coding challenges"],
    [stats.paths, "catalog paths"],
    [stats.concepts, "graph concepts"],
  ].filter(([value]) => Number(value) > 0);
  if (items.length === 0) return null;
  return (
    <section aria-label="Knowledge Pack counts" className="border-y border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950">
      <div className="mx-auto grid max-w-site gap-4 px-5 py-6 sm:grid-cols-2 lg:grid-cols-5">
        {items.map(([value, label]) => (
          <p key={String(label)} className="text-center">
            <span className="block font-display text-2xl tracking-tight">{formatCount(Number(value))}</span>
            <span className="text-sm text-slate-600 dark:text-slate-400">{label}</span>
          </p>
        ))}
      </div>
      <p className="px-5 pb-5 text-center text-sm text-slate-600 dark:text-slate-400">{stats.note}</p>
    </section>
  );
}
