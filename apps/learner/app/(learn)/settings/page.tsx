"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { api, ApiError } from "@/lib/api";
import { useStudio } from "@/stores/studio";

type Account = {
  display_name: string;
  handle: string | null;
  locale: "en" | "fr" | "es";
  timezone: string;
  country_code: string | null;
  leaderboard_opt_out: boolean;
};

type Prefs = {
  career_goal: string | null;
  learning_style: "visual" | "reading" | "hands_on" | "auditory" | "balanced";
  weekly_minutes: number | null;
  cost_preference: "free_only" | "any";
  maths_comfort: "none" | "light" | "moderate" | "formal" | null;
  programming_experience: "none" | "some" | "daily" | null;
  tutor_mode: "socratic" | "direct";
};

type Academy = { slug: string; title: string; summary: string };

const styles = [
  ["balanced", "A mix"],
  ["reading", "Reading"],
  ["hands_on", "Hands-on"],
  ["visual", "Visual"],
  ["auditory", "Listening"],
] as const;

const zones = [
  "UTC",
  "Africa/Lagos",
  "Africa/Nairobi",
  "Europe/London",
  "Europe/Paris",
  "America/New_York",
  "America/Los_Angeles",
  "Asia/Kolkata",
  "Asia/Singapore",
];

const inputClass =
  "mt-1 w-full rounded-full border border-slate-300 bg-white px-3 py-2 dark:border-slate-600 dark:bg-slate-950";

export default function SettingsPage() {
  const client = useQueryClient();
  const devUserId = useStudio((state) => state.devUserId);
  const me = useQuery({
    queryKey: ["me", devUserId],
    queryFn: () => api<Account>("/api/v1/me"),
  });
  const prefs = useQuery({
    queryKey: ["prefs", devUserId],
    queryFn: () => api<Prefs>("/api/v1/me/learning-preferences"),
  });
  const academies = useQuery({
    queryKey: ["academies", devUserId],
    queryFn: () => api<Academy[]>("/api/v1/learn/academies"),
  });
  const [account, setAccount] = useState<Account | null>(null);
  const [learning, setLearning] = useState<Prefs | null>(null);
  const [note, setNote] = useState<string | null>(null);
  useEffect(() => {
    if (me.data) setAccount(me.data);
  }, [me.data]);
  useEffect(() => {
    if (prefs.data) setLearning(prefs.data);
  }, [prefs.data]);

  const save = useMutation({
    mutationFn: async () => {
      if (!account || !learning) return;
      await api("/api/v1/me", {
        method: "PATCH",
        body: JSON.stringify({
          display_name: account.display_name,
          handle: account.handle || undefined,
          locale: account.locale,
          timezone: account.timezone,
          country_code: account.country_code || undefined,
          leaderboard_opt_out: account.leaderboard_opt_out,
        }),
      });
      await api("/api/v1/me/learning-preferences", {
        method: "PATCH",
        body: JSON.stringify({
          career_goal: learning.career_goal,
          learning_style: learning.learning_style,
          weekly_minutes: learning.weekly_minutes,
          cost_preference: learning.cost_preference,
          maths_comfort: learning.maths_comfort,
          programming_experience: learning.programming_experience,
          tutor_mode: learning.tutor_mode,
        }),
      });
    },
    onSuccess: () => {
      setNote("Saved. The next tutor reply, catalog ranking, and study plan use these.");
      client.invalidateQueries({ queryKey: ["me"] });
      client.invalidateQueries({ queryKey: ["prefs"] });
      client.invalidateQueries({ queryKey: ["dashboard"] });
      client.invalidateQueries({ queryKey: ["academies"] });
      client.invalidateQueries({ queryKey: ["catalog-recs"] });
    },
  });

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    setNote(null);
    save.mutate();
  }

  if (me.isLoading || prefs.isLoading) return <p>Loading your settings…</p>;
  if (!account || !learning) {
    const message = me.error instanceof ApiError ? me.error.message : "Settings are unavailable.";
    return <p>{message}</p>;
  }

  return (
    <form className="mx-auto max-w-2xl space-y-8" onSubmit={onSubmit}>
      <header>
        <h1 className="font-display text-4xl tracking-tight">Settings</h1>
        <p className="mt-2 text-slate-600 dark:text-slate-300">
          These change how the tutor teaches, which catalog items rise, and how dense a study
          plan is. Nothing here awards XP.
        </p>
      </header>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Profile</h2>
        <label className="block text-sm font-semibold">
          Display name
          <input
            className={inputClass}
            value={account.display_name}
            onChange={(event) => setAccount({ ...account, display_name: event.target.value })}
            required
            minLength={2}
            maxLength={120}
          />
        </label>
        <label className="block text-sm font-semibold">
          Handle
          <input
            className={inputClass}
            value={account.handle || ""}
            onChange={(event) => setAccount({ ...account, handle: event.target.value || null })}
            pattern="[A-Za-z0-9_]{3,24}"
            placeholder="optional"
          />
        </label>
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="block text-sm font-semibold">
            Language
            <select
              className={inputClass}
              value={account.locale}
              onChange={(event) =>
                setAccount({ ...account, locale: event.target.value as Account["locale"] })
              }
            >
              <option value="en">English</option>
              <option value="fr">Français</option>
              <option value="es">Español</option>
            </select>
          </label>
          <label className="block text-sm font-semibold">
            Time zone
            <select
              className={inputClass}
              value={account.timezone}
              onChange={(event) => setAccount({ ...account, timezone: event.target.value })}
            >
              {[account.timezone, ...zones.filter((zone) => zone !== account.timezone)].map(
                (zone) => (
                  <option key={zone} value={zone}>
                    {zone}
                  </option>
                ),
              )}
            </select>
          </label>
        </div>
        <label className="block text-sm font-semibold">
          Country (ISO code)
          <input
            className={`${inputClass} uppercase`}
            value={account.country_code || ""}
            maxLength={2}
            onChange={(event) =>
              setAccount({ ...account, country_code: event.target.value.toUpperCase() || null })
            }
            placeholder="GB"
          />
        </label>
        <label className="flex items-center gap-2 text-sm font-semibold">
          <input
            type="checkbox"
            checked={account.leaderboard_opt_out}
            onChange={(event) =>
              setAccount({ ...account, leaderboard_opt_out: event.target.checked })
            }
          />
          Keep me off public leaderboards
        </label>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">How you learn</h2>
        <fieldset>
          <legend className="text-sm font-semibold">Goal academy</legend>
          <div className="mt-2 space-y-2">
            {(academies.data || []).map((item) => (
              <label
                key={item.slug}
                className="block rounded-3xl border border-slate-200 p-3 dark:border-slate-700"
              >
                <input
                  className="mr-2"
                  type="radio"
                  name="academy"
                  checked={learning.career_goal === item.slug}
                  onChange={() => setLearning({ ...learning, career_goal: item.slug })}
                />
                <span className="font-semibold">{item.title}</span>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{item.summary}</p>
              </label>
            ))}
          </div>
        </fieldset>
        <fieldset>
          <legend className="text-sm font-semibold">Style</legend>
          <div className="mt-2 flex flex-wrap gap-2">
            {styles.map(([value, label]) => (
              <label key={value} className="text-sm font-semibold">
                <input
                  className="mr-1"
                  type="radio"
                  name="style"
                  checked={learning.learning_style === value}
                  onChange={() => setLearning({ ...learning, learning_style: value })}
                />
                {label}
              </label>
            ))}
          </div>
        </fieldset>
        <fieldset>
          <legend className="text-sm font-semibold">Maths comfort</legend>
          <div className="mt-2 flex flex-wrap gap-2">
            {(["none", "light", "moderate", "formal"] as const).map((value) => (
              <label key={value} className="text-sm font-semibold">
                <input
                  className="mr-1"
                  type="radio"
                  name="maths"
                  checked={learning.maths_comfort === value}
                  onChange={() => setLearning({ ...learning, maths_comfort: value })}
                />
                {value}
              </label>
            ))}
          </div>
        </fieldset>
        <fieldset>
          <legend className="text-sm font-semibold">Programming</legend>
          <div className="mt-2 flex flex-wrap gap-2">
            {(["none", "some", "daily"] as const).map((value) => (
              <label key={value} className="text-sm font-semibold">
                <input
                  className="mr-1"
                  type="radio"
                  name="programming"
                  checked={learning.programming_experience === value}
                  onChange={() => setLearning({ ...learning, programming_experience: value })}
                />
                {value}
              </label>
            ))}
          </div>
        </fieldset>
        <label className="block text-sm font-semibold">
          Minutes a week
          <select
            className={inputClass}
            value={learning.weekly_minutes ?? ""}
            onChange={(event) =>
              setLearning({
                ...learning,
                weekly_minutes: event.target.value ? Number(event.target.value) : null,
              })
            }
          >
            <option value="">Not set</option>
            <option value="30">30 — a short session</option>
            <option value="60">60 — one sitting</option>
            <option value="120">120 — a couple of evenings</option>
            <option value="180">180 — a focused week</option>
            <option value="300">300 — daily practice</option>
          </select>
        </label>
        <fieldset>
          <legend className="text-sm font-semibold">Catalog cost</legend>
          <div className="mt-2 flex flex-wrap gap-3">
            <label className="text-sm font-semibold">
              <input
                className="mr-1"
                type="radio"
                name="cost"
                checked={learning.cost_preference === "any"}
                onChange={() => setLearning({ ...learning, cost_preference: "any" })}
              />
              Free and paid
            </label>
            <label className="text-sm font-semibold">
              <input
                className="mr-1"
                type="radio"
                name="cost"
                checked={learning.cost_preference === "free_only"}
                onChange={() => setLearning({ ...learning, cost_preference: "free_only" })}
              />
              Free only
            </label>
          </div>
        </fieldset>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">Tutor</h2>
        <fieldset>
          <legend className="text-sm font-semibold">Default mode</legend>
          <div className="mt-2 flex gap-3">
            {(["socratic", "direct"] as const).map((value) => (
              <label key={value} className="text-sm font-semibold">
                <input
                  className="mr-1"
                  type="radio"
                  name="tutor"
                  checked={learning.tutor_mode === value}
                  onChange={() => setLearning({ ...learning, tutor_mode: value })}
                />
                {value === "socratic" ? "Socratic" : "Direct"}
              </label>
            ))}
          </div>
        </fieldset>
        <p className="text-sm text-slate-600 dark:text-slate-300">
          Socratic asks first. Direct explains, then gives an exercise. Stages 0–1 of a new
          Socratic thread stay scripted.
        </p>
      </section>

      <p className="text-sm">
        Placement is optional and awards no XP.{" "}
        <Link className="font-semibold text-[#1d4ed8] underline" href="/onboarding">
          Retake the placement check
        </Link>
        .
      </p>

      <Button type="submit" disabled={save.isPending}>
        {save.isPending ? "Saving…" : "Save"}
      </Button>
      {note ? <p className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">{note}</p> : null}
      {save.error ? (
        <p className="text-sm text-red-800 dark:text-red-300">
          {save.error instanceof ApiError ? save.error.message : save.error.message}
        </p>
      ) : null}
    </form>
  );
}
