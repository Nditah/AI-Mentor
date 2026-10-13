"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { api, ApiError } from "@/lib/api";
import { useStudio } from "@/stores/studio";

type Academy = { slug: string; title: string; summary: string };
type Question = { id: string; prompt: string; options: string[]; academy_slug: string };
type Onboarding = {
  onboarded: boolean;
  academies: Academy[];
  questions: Question[];
  preferences: { learning_style: string; career_goal: string | null };
};
type Result = {
  onboarded: boolean;
  recommended: { slug: string; title: string; href: string };
  diagnostic: { asked: number; correct: number; skipped: boolean };
};

const styles = [
  ["balanced", "A mix"],
  ["reading", "Reading"],
  ["hands_on", "Hands-on"],
  ["visual", "Visual"],
  ["auditory", "Listening"],
] as const;

export default function OnboardingPage() {
  const client = useQueryClient();
  const devUserId = useStudio((state) => state.devUserId);
  const query = useQuery({
    queryKey: ["onboarding", devUserId],
    queryFn: () => api<Onboarding>("/api/v1/onboarding"),
  });
  const [step, setStep] = useState(0);
  const [academy, setAcademy] = useState("");
  const [style, setStyle] = useState<(typeof styles)[number][0]>("balanced");
  const [maths, setMaths] = useState<"none" | "light" | "moderate" | "formal" | "">("");
  const [programming, setProgramming] = useState<"none" | "some" | "daily" | "">("");
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [result, setResult] = useState<Result | null>(null);
  useEffect(() => {
    if (academy || !query.data?.academies[0]) return;
    setAcademy(query.data.preferences.career_goal || query.data.academies[0].slug);
  }, [academy, query.data]);
  const submit = useMutation({
    mutationFn: (payload: { skip: boolean }) =>
      api<Result>("/api/v1/onboarding", {
        method: "POST",
        body: JSON.stringify({
          academy_slug: academy,
          learning_style: style,
          maths_comfort: maths || null,
          programming_experience: programming || null,
          answers: payload.skip
            ? []
            : Object.entries(answers).map(([id, response]) => ({ id, response })),
        }),
      }),
    onSuccess: (body) => {
      setResult(body);
      client.invalidateQueries({ queryKey: ["dashboard"] });
      client.invalidateQueries({ queryKey: ["onboarding"] });
    },
  });

  if (query.isLoading) return <p>Loading onboarding…</p>;
  if (query.error) {
    const message = query.error instanceof ApiError ? query.error.message : "Onboarding is unavailable.";
    return <p>{message}</p>;
  }
  const data = query.data!;

  if (result) {
    return (
      <section className="max-w-xl space-y-4">
        <h1 className="font-display text-4xl tracking-tight">You are ready to start</h1>
        <p className="text-slate-700 dark:text-slate-300">
          {result.diagnostic.skipped
            ? "You skipped the placement check. You can retake it any time from this page."
            : `Placement check: ${result.diagnostic.correct} of ${result.diagnostic.asked} correct. This is a starting point, not a grade.`}
        </p>
        <p>
          Recommended academy:{" "}
          <Link className="font-semibold text-[#1d4ed8] underline" href={result.recommended.href}>
            {result.recommended.title}
          </Link>
        </p>
        <Button href={result.recommended.href}>Open the academy</Button>
        <p className="text-sm">
          Change style, maths, time, or academy later in{" "}
          <Link className="font-semibold text-[#1d4ed8] underline" href="/settings">
            Settings
          </Link>
          .
        </p>
      </section>
    );
  }

  return (
    <div className="max-w-2xl space-y-6">
      <h1 className="font-display text-4xl tracking-tight">Start in the right place</h1>
      <p className="text-slate-600 dark:text-slate-300">
        Under five minutes. Language and academy are the only required answers. The placement check is optional and does not award XP.
      </p>
      {step === 0 ? (
        <fieldset className="space-y-3">
          <legend className="font-semibold">Which academy is your goal?</legend>
          {data.academies.map((item) => (
            <label key={item.slug} className="block rounded-3xl border border-slate-200 p-4 dark:border-slate-700">
              <input
                className="mr-2"
                type="radio"
                name="academy"
                checked={academy === item.slug}
                onChange={() => setAcademy(item.slug)}
              />
              <span className="font-semibold">{item.title}</span>
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{item.summary}</p>
            </label>
          ))}
          <Button type="button" onClick={() => setStep(1)} disabled={!academy}>
            Continue
          </Button>
        </fieldset>
      ) : null}
      {step === 1 ? (
        <div className="space-y-4">
          <fieldset>
            <legend className="font-semibold">How do you prefer to learn?</legend>
            <div className="mt-2 flex flex-wrap gap-2">
              {styles.map(([value, label]) => (
                <label key={value} className="text-sm font-semibold">
                  <input className="mr-1" type="radio" name="style" checked={style === value} onChange={() => setStyle(value)} />
                  {label}
                </label>
              ))}
            </div>
          </fieldset>
          <fieldset>
            <legend className="font-semibold">Maths comfort (optional)</legend>
            <div className="mt-2 flex flex-wrap gap-2">
              {(["none", "light", "moderate", "formal"] as const).map((value) => (
                <label key={value} className="text-sm font-semibold">
                  <input className="mr-1" type="radio" name="maths" checked={maths === value} onChange={() => setMaths(value)} />
                  {value}
                </label>
              ))}
            </div>
          </fieldset>
          <fieldset>
            <legend className="font-semibold">Programming (optional)</legend>
            <div className="mt-2 flex flex-wrap gap-2">
              {(["none", "some", "daily"] as const).map((value) => (
                <label key={value} className="text-sm font-semibold">
                  <input
                    className="mr-1"
                    type="radio"
                    name="programming"
                    checked={programming === value}
                    onChange={() => setProgramming(value)}
                  />
                  {value}
                </label>
              ))}
            </div>
          </fieldset>
          <div className="flex gap-2">
            <Button type="button" variant="quiet" onClick={() => setStep(0)}>
              Back
            </Button>
            <Button type="button" onClick={() => setStep(2)}>
              Placement check
            </Button>
            <Button type="button" variant="ghost" disabled={submit.isPending} onClick={() => submit.mutate({ skip: true })}>
              Skip check
            </Button>
          </div>
        </div>
      ) : null}
      {step === 2 ? (
        <div className="space-y-4">
          <p className="text-sm text-slate-600 dark:text-slate-300">
            This just helps us start in the right place. Wrong answers do not cost a streak or XP.
          </p>
          {data.questions.map((item) => (
            <fieldset key={item.id} className="rounded-3xl border border-slate-200 p-4 dark:border-slate-700">
              <legend className="font-semibold">{item.prompt}</legend>
              <div className="mt-2 space-y-1">
                {item.options.map((option) => {
                  const letter = option.slice(0, 1);
                  return (
                    <label key={option} className="block text-sm">
                      <input
                        className="mr-2"
                        type="radio"
                        name={item.id}
                        checked={answers[item.id] === letter}
                        onChange={() => setAnswers((current) => ({ ...current, [item.id]: letter }))}
                      />
                      {option}
                    </label>
                  );
                })}
              </div>
            </fieldset>
          ))}
          <div className="flex gap-2">
            <Button type="button" variant="quiet" onClick={() => setStep(1)}>
              Back
            </Button>
            <Button type="button" disabled={submit.isPending} onClick={() => submit.mutate({ skip: false })}>
              See my start
            </Button>
          </div>
        </div>
      ) : null}
      {submit.error ? (
        <p className="text-sm text-red-800 dark:text-red-300">
          {submit.error instanceof ApiError ? submit.error.message : submit.error.message}
        </p>
      ) : null}
    </div>
  );
}
