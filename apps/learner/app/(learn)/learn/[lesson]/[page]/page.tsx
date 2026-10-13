"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { use, useEffect, useRef, useState } from "react";
import { MentorMarkdown } from "@/components/markdown-view";
import { Button } from "@/components/ui/button";
import { ApiError, api } from "@/lib/api";
import { useStudio } from "@/stores/studio";

type Crumb = { label: string; href: string | null };
type Question = { id: string; kind: string; prompt: string; options: string[] };
type Check = { id: string; title: string; pass_score: number; passed: boolean; questions: Question[] };
type Result = { question_id: string; correct: boolean; explanation: string };
type CatalogItem = {
  asset_id: string;
  title: string;
  url: string;
  kind: string;
  tags: string[];
  topic: string;
  skills: string[];
};
type Payload = {
  breadcrumbs: Crumb[];
  objectives: string[];
  resources: { heading: string; items: CatalogItem[] }[];
  outline: {
    module: string | null;
    lessons: { slug: string; title: string; current: boolean; progress: number }[];
    pages: { slug: string; title: string; current: boolean; completed: boolean }[];
  };
  page: {
    id: string;
    slug: string;
    title: string;
    kind: string;
    body_md: string;
    estimated_minutes: number;
    index: number;
    total: number;
    bookmarked: boolean;
    note: string;
    check: Check | null;
    asset: CatalogItem | null;
  };
  progress: { lesson: number; module: number; course: number; path: number };
  previous: { lesson: string; page: string } | null;
  next: { lesson: string; page: string } | null;
  lesson: { slug: string; title: string };
};

export default function TopicPage({ params }: { params: Promise<{ lesson: string; page: string }> }) {
  const { lesson, page } = use(params);
  const devUserId = useStudio((state) => state.devUserId);
  const client = useQueryClient();
  const started = useRef(Date.now());
  const query = useQuery({
    queryKey: ["topic", lesson, page, devUserId],
    queryFn: () => api<Payload>(`/api/v1/learn/lessons/${lesson}/pages/${page}`),
  });
  const [note, setNote] = useState("");
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [feedback, setFeedback] = useState<Result[] | null>(null);
  const [message, setMessage] = useState("");

  useEffect(() => {
    started.current = Date.now();
    setFeedback(null);
    setAnswers({});
    setMessage("");
  }, [lesson, page]);

  useEffect(() => {
    if (query.data) setNote(query.data.page.note);
  }, [query.data]);

  const complete = useMutation({
    mutationFn: (pageId: string) =>
      api(`/api/v1/learn/pages/${pageId}/complete`, {
        method: "POST",
        body: JSON.stringify({ seconds: Math.round((Date.now() - started.current) / 1000) }),
      }),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["topic", lesson] });
      client.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
  const bookmark = useMutation({
    mutationFn: (pageId: string) => api(`/api/v1/learn/pages/${pageId}/bookmark`, { method: "POST" }),
    onSuccess: () => client.invalidateQueries({ queryKey: ["topic", lesson, page] }),
  });
  const saveNote = useMutation({
    mutationFn: (pageId: string) =>
      api(`/api/v1/learn/pages/${pageId}/notes`, { method: "PUT", body: JSON.stringify({ body: note }) }),
  });
  const grade = useMutation({
    mutationFn: (check: Check) =>
      api<{ passed: boolean; score: number; results: Result[]; xp: number }>(`/api/v1/learn/checks/${check.id}`, {
        method: "POST",
        body: JSON.stringify({
          answers: check.questions.map((question) => ({
            question_id: question.id,
            response: answers[question.id] || "",
          })),
        }),
      }),
    onSuccess: (result) => {
      setFeedback(result.results);
      setMessage(result.passed ? `Passed at ${result.score}%. ${result.xp ? `+${result.xp} XP.` : ""}` : `Scored ${result.score}%. Try again.`);
      client.invalidateQueries({ queryKey: ["topic", lesson, page] });
    },
  });

  if (query.isLoading) return <p>Loading the page…</p>;
  if (query.error) {
    const text = query.error instanceof ApiError ? query.error.message : "That page was not found.";
    return <p>{text}</p>;
  }
  if (!query.data) return <p>That page was not found.</p>;
  const data = query.data;
  const current = data.page;
  const href = (target: { lesson: string; page: string }) => `/learn/${target.lesson}/${target.page}`;

  async function goNext() {
    try {
      await complete.mutateAsync(current.id);
      if (data.next) window.location.assign(href(data.next));
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : "This page is not complete yet.");
    }
  }

  return (
    <div className="lg:grid lg:grid-cols-[220px_minmax(0,1fr)_240px] lg:items-start lg:gap-6">
      <aside className="mb-6 lg:sticky lg:top-4 lg:max-h-[calc(100vh-2rem)] lg:overflow-auto" aria-label="Lesson outline">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{data.outline.module}</p>
        <ul className="mt-2 space-y-1 text-sm">
          {data.outline.lessons.map((item) => (
            <li key={item.slug} className={item.current ? "font-semibold" : ""}>
              {item.title} · {item.progress}%
            </li>
          ))}
        </ul>
        <p className="mt-4 text-xs font-semibold uppercase tracking-wide text-slate-500">Pages</p>
        <ol className="mt-2 space-y-1 text-sm">
          {data.outline.pages.map((item) => (
            <li key={item.slug}>
              <Link className={item.current ? "font-semibold underline" : "underline"} href={`/learn/${lesson}/${item.slug}`} aria-current={item.current ? "page" : undefined}>
                {item.completed ? "Done · " : ""}{item.title}
              </Link>
            </li>
          ))}
        </ol>
      </aside>
      <article className="min-w-0">
        <nav aria-label="Breadcrumb" className="text-sm">
          <ol className="flex flex-wrap gap-x-2 gap-y-1">
            {data.breadcrumbs.map((crumb) => (
              <li key={crumb.label}>
                {crumb.href ? <Link className="underline" href={crumb.href}>{crumb.label}</Link> : <span aria-current="page">{crumb.label}</span>}
                {crumb.href ? <span aria-hidden="true"> /</span> : null}
              </li>
            ))}
          </ol>
        </nav>
        <p className="mt-3 text-sm font-semibold text-[#1d4ed8]">
          Page {current.index} of {current.total} · {current.estimated_minutes} min · lesson {data.progress.lesson}%
        </p>
        <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800" role="meter" aria-label="Lesson progress" aria-valuenow={data.progress.lesson} aria-valuemin={0} aria-valuemax={100}>
          <div className="h-full bg-[#1d4ed8]" style={{ width: `${data.progress.lesson}%` }} />
        </div>
        <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
          <h1 className="font-display text-4xl tracking-tight">{current.title}</h1>
          <Button type="button" variant="quiet" onClick={() => bookmark.mutate(current.id)}>
            {current.bookmarked ? "Bookmarked" : "Bookmark"}
          </Button>
        </div>
        <div className="mt-4 max-w-[68ch]">
          <MentorMarkdown content={current.body_md} />
        </div>
        {current.asset ? (
          <section className="mt-6 max-w-[68ch] rounded-2xl border border-slate-200 p-4 dark:border-slate-700">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{current.asset.kind.replaceAll("_", " ")}</p>
            {current.asset.url ? (
              <a className="mt-1 block text-lg font-semibold underline" href={current.asset.url}>
                {current.asset.title}
              </a>
            ) : (
              <p className="mt-1 text-lg font-semibold">{current.asset.title}</p>
            )}
            {current.asset.skills.length ? (
              <p className="mt-2 text-sm">Skills: {current.asset.skills.join(", ")}</p>
            ) : null}
          </section>
        ) : null}
        {current.check ? (
          <form
            className="mt-6 space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              grade.mutate(current.check!);
            }}
          >
            <h2 className="text-xl font-semibold">{current.check.title}</h2>
            <p className="text-sm">Pass mark {current.check.pass_score}%. {current.check.passed ? "You have passed this check." : ""}</p>
            {current.check.questions.map((question) => (
              <fieldset key={question.id} className="rounded-2xl border border-slate-200 p-4 dark:border-slate-700">
                <legend className="font-semibold">{question.prompt}</legend>
                {question.kind === "short" || question.kind === "fill" ? (
                  <input
                    className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 dark:border-slate-600 dark:bg-slate-950"
                    aria-label={question.prompt}
                    value={answers[question.id] || ""}
                    onChange={(event) => setAnswers({ ...answers, [question.id]: event.target.value })}
                  />
                ) : (
                  <div className="mt-2 space-y-1">
                    {question.options.map((option) => {
                      const value = question.kind === "true_false" ? option.toLowerCase() : option.slice(0, 1).toLowerCase();
                      return (
                        <label key={option} className="flex gap-2">
                          <input
                            type="radio"
                            name={question.id}
                            value={value}
                            checked={answers[question.id] === value}
                            onChange={() => setAnswers({ ...answers, [question.id]: value })}
                          />
                          <span>{option}</span>
                        </label>
                      );
                    })}
                  </div>
                )}
                {feedback?.find((item) => item.question_id === question.id) ? (
                  <p className="mt-2 text-sm">
                    {feedback.find((item) => item.question_id === question.id)?.correct ? "Correct. " : "Not yet. "}
                    {feedback.find((item) => item.question_id === question.id)?.explanation}
                  </p>
                ) : null}
              </fieldset>
            ))}
            <Button type="submit" disabled={grade.isPending}>Check answers</Button>
          </form>
        ) : null}
        {message ? <p className="mt-4" role="status">{message}</p> : null}
        <div className="mt-8 flex items-center justify-between gap-3">
          {data.previous ? <Button variant="quiet" href={href(data.previous)}>Previous</Button> : <span />}
          {data.next ? (
            <Button type="button" onClick={goNext} disabled={complete.isPending}>Next</Button>
          ) : (
            <Button type="button" onClick={goNext} disabled={complete.isPending}>Lesson complete</Button>
          )}
        </div>
      </article>
      <aside className="mt-8 space-y-4 lg:sticky lg:top-4 lg:mt-0 lg:max-h-[calc(100vh-2rem)] lg:overflow-auto" aria-label="Lesson support">
        <section className="rounded-2xl border border-slate-200 p-4 dark:border-slate-700">
          <h2 className="font-semibold">Progress</h2>
          <ul className="mt-2 text-sm">
            <li>Lesson {data.progress.lesson}%</li>
            <li>Module {data.progress.module}%</li>
            <li>Course {data.progress.course}%</li>
            <li>Path {data.progress.path}%</li>
          </ul>
        </section>
        {data.objectives.length ? (
          <section className="rounded-2xl border border-slate-200 p-4 dark:border-slate-700">
            <h2 className="font-semibold">Learning objectives</h2>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
              {data.objectives.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </section>
        ) : null}
        {data.resources.map((group) => (
          <section key={group.heading} className="rounded-2xl border border-slate-200 p-4 dark:border-slate-700">
            <h2 className="font-semibold">{group.heading}</h2>
            <ul className="mt-2 space-y-1 text-sm">
              {group.items.map((item) => (
                <li key={item.asset_id}>
                  {item.url ? <a className="underline" href={item.url}>{item.title}</a> : item.title}
                  <span className="text-slate-500"> · {item.kind.replaceAll("_", " ")}</span>
                </li>
              ))}
            </ul>
          </section>
        ))}
        <section className="rounded-2xl border border-slate-200 p-4 dark:border-slate-700">
          <h2 className="font-semibold">Notes</h2>
          <label className="mt-2 block text-sm">
            <span className="sr-only">Notes for this page</span>
            <textarea
              className="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 dark:border-slate-600 dark:bg-slate-950"
              rows={5}
              value={note}
              onChange={(event) => setNote(event.target.value)}
              onBlur={() => saveNote.mutate(current.id)}
            />
          </label>
        </section>
      </aside>
    </div>
  );
}
