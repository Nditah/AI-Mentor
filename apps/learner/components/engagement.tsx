export function ProgressRing({
  percent,
  label,
}: {
  percent: number;
  label: string;
}) {
  const clamped = Math.max(0, Math.min(100, percent));
  const offset = 120 - (120 * clamped) / 100;
  return (
    <div className="flex items-center gap-3" aria-label={label}>
      <svg className="progress-ring h-14 w-14" viewBox="0 0 44 44" aria-hidden>
        <circle cx="22" cy="22" r="19" fill="none" stroke="currentColor" className="text-slate-200 dark:text-slate-700" strokeWidth="4" />
        <circle
          cx="22"
          cy="22"
          r="19"
          fill="none"
          stroke="#10B981"
          strokeWidth="4"
          strokeLinecap="round"
          className="meter"
          style={{ ["--ring-offset" as string]: offset }}
          transform="rotate(-90 22 22)"
        />
      </svg>
      <p className="text-sm font-semibold">{clamped}% complete</p>
    </div>
  );
}

export function MentorMark({ stage }: { stage: string }) {
  const rings = { novice: 1, practitioner: 2, expert: 3, research: 4, grandmaster: 5 }[stage] || 1;
  return (
    <div className="flex h-16 w-16 items-center justify-center" aria-hidden>
      <div className="relative flex h-14 w-14 items-center justify-center">
        {Array.from({ length: rings }).map((_, index) => (
          <span
            key={index}
            className="absolute rounded-full border-2 border-[#6D28D9]"
            style={{ inset: index * 5, opacity: 0.3 + index * 0.15 }}
          />
        ))}
        <span className="h-3 w-3 rounded-full bg-[#1D4ED8]" />
      </div>
    </div>
  );
}

export function SkillCardView({
  name,
  description,
  tier,
  mastery,
  difficulty,
}: {
  name: string;
  description: string;
  tier: string;
  mastery: number;
  difficulty: string;
}) {
  const tone =
    tier === "gold"
      ? "border-amber-400 bg-amber-50 dark:bg-amber-950/40"
      : tier === "silver"
        ? "border-slate-400 bg-slate-50 dark:bg-slate-900"
        : "border-emerald-400 bg-emerald-50 dark:bg-emerald-950/30";
  return (
    <article className={`card-reveal rounded-3xl border-2 p-4 ${tone}`}>
      <p className="text-xs font-semibold uppercase tracking-wide">{tier} card</p>
      <h3 className="mt-1 text-lg font-semibold">{name}</h3>
      <p className="mt-2 text-sm text-slate-700 dark:text-slate-300">{description}</p>
      <p className="mt-3 text-sm font-semibold">
        Mastery {mastery} · {difficulty}
      </p>
    </article>
  );
}

export function StreakFlame({ days, freezes }: { days: number; freezes: number }) {
  return (
    <p className="text-sm">
      <span className="font-semibold">{days}-day streak</span>
      {freezes ? ` · ${freezes} freeze${freezes === 1 ? "" : "s"} ready` : ""}
    </p>
  );
}
