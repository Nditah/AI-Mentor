"use client";

import { use } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";

type Step = {
  position: number;
  kind: string;
  title: string;
  concept_slug: string | null;
  estimated_minutes: number | null;
  optional: boolean;
};

type Challenge = {
  language: string;
  entrypoint: string;
  variant: string;
  starter_code: string;
  visible_tests: unknown[];
  hidden_test_count: number;
  has_reference: boolean;
};

type Resource = {
  id: string;
  title: string;
  description: string;
  resource_type_label: string;
  category: string;
  topic: string;
  provider: string;
  author: string;
  url: string | null;
  difficulty: string;
  quality_score: number;
  licence: string;
  concepts: string[];
  skills: string[];
  prerequisites: string[];
  learning_outcomes: string[];
  body_md: string;
  steps?: Step[];
  challenge?: Challenge;
};

export default function CatalogDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const query = useQuery({
    queryKey: ["resource", id],
    queryFn: () => api<Resource>(`/api/v1/resources/${id}`),
    retry: false,
  });
  if (query.error instanceof ApiError) return <p>{query.error.message}</p>;
  if (!query.data) return <p>Loading the resource…</p>;
  const item = query.data;
  return (
    <article className="max-w-3xl">
      <p className="text-sm font-semibold uppercase tracking-wide text-[#1d4ed8]">
        {item.resource_type_label} · quality {item.quality_score}
      </p>
      <h1 className="mt-1 text-3xl font-semibold tracking-tight">{item.title}</h1>
      <p className="mt-2 text-slate-700 dark:text-slate-300">{item.description}</p>
      <p className="mt-2 text-sm">
        {item.difficulty} · {item.category} · {item.topic || "No topic"} · {item.provider || "—"} ·{" "}
        {item.licence}
      </p>
      {item.author ? <p className="text-sm">Author {item.author}</p> : null}
      {item.url ? (
        <p className="mt-2 text-sm">
          <a className="underline" href={item.url} rel="noreferrer" target="_blank">
            Open source
          </a>
        </p>
      ) : null}
      {item.concepts?.length ? (
        <p className="mt-3 text-sm">Concepts: {item.concepts.join(", ")}</p>
      ) : null}
      {item.skills?.length ? <p className="text-sm">Skills: {item.skills.join(", ")}</p> : null}
      {item.prerequisites?.length ? (
        <p className="text-sm">Prerequisites: {item.prerequisites.join(", ")}</p>
      ) : null}
      {item.learning_outcomes?.length ? (
        <section className="mt-6">
          <h2 className="text-xl font-semibold">Outcomes</h2>
          <ul className="mt-2 list-disc pl-5 text-sm">
            {item.learning_outcomes.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </section>
      ) : null}
      {item.steps?.length ? (
        <section className="mt-6">
          <h2 className="text-xl font-semibold">Path outline</h2>
          <ol className="mt-2 space-y-1 text-sm">
            {item.steps.map((step) => (
              <li key={`${step.position}-${step.title}`}>
                <span className="font-semibold">{step.position}. {step.title}</span>
                <span className="text-slate-600 dark:text-slate-300">
                  {` · ${step.kind}`}
                  {step.concept_slug ? ` · ${step.concept_slug}` : ""}
                  {step.optional ? " · optional" : ""}
                </span>
              </li>
            ))}
          </ol>
        </section>
      ) : null}
      {item.challenge ? (
        <section className="mt-6">
          <h2 className="text-xl font-semibold">Challenge spec</h2>
          <p className="mt-2 text-sm">
            {item.challenge.language} · {item.challenge.variant} · {item.challenge.entrypoint}
            {` · ${item.challenge.hidden_test_count} hidden tests`}
            {item.challenge.has_reference ? " · reference solution stored server-side" : ""}
          </p>
          <pre className="mt-3 overflow-x-auto rounded-2xl bg-white p-4 text-sm dark:bg-slate-900">
            {item.challenge.starter_code || "No starter code."}
          </pre>
        </section>
      ) : null}
      {item.body_md ? (
        <section className="mt-6">
          <h2 className="text-xl font-semibold">Notes</h2>
          <pre className="mt-2 whitespace-pre-wrap rounded-2xl bg-white p-4 text-sm dark:bg-slate-900">
            {item.body_md}
          </pre>
        </section>
      ) : null}
      <p className="mt-8 text-sm">
        <Link className="underline" href="/catalog">
          Back to catalog
        </Link>
      </p>
    </article>
  );
}
