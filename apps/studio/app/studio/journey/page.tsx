"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { api } from "@/lib/api";

type Course = { slug: string; title: string };
type Path = { slug: string; title: string; courses: Course[] };
type Academy = { slug: string; title: string; paths: Path[] };

const learner = process.env.NEXT_PUBLIC_LEARNER_URL || "http://localhost:3000";

export default function JourneyAuthorPage() {
  const client = useQueryClient();
  const query = useQuery({
    queryKey: ["journey-outline"],
    queryFn: () => api<Academy[]>("/api/v1/content/journey"),
  });
  const [lesson, setLesson] = useState("what-is-a-state");
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [kind, setKind] = useState("reading");
  const [assetUrl, setAssetUrl] = useState("");
  const [notice, setNotice] = useState("");
  const add = useMutation({
    mutationFn: () =>
      api<{ slug: string }>("/api/v1/content/journey/pages", {
        method: "POST",
        body: JSON.stringify({
          lesson_slug: lesson,
          title,
          body_md: body,
          kind,
          asset_url: assetUrl,
        }),
      }),
    onSuccess: (created) => {
      setNotice(`Added “${title}”. Preview ${learner}/learn/${lesson}/${created.slug}`);
      setTitle("");
      setBody("");
      client.invalidateQueries({ queryKey: ["journey-outline"] });
    },
  });

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    add.mutate();
  }

  return (
    <div>
      <h1 className="text-3xl font-semibold tracking-tight">Learning journey</h1>
      <p className="mt-2 max-w-2xl text-slate-600 dark:text-slate-300">
        Academies, paths, courses, modules, and lessons. Add a topic page to a lesson, then open the learner preview.
      </p>
      {query.isLoading ? <p className="mt-6">Loading the journey…</p> : null}
      <div className="mt-6 space-y-4">
        {(query.data || []).map((academy) => (
          <section key={academy.slug} className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
            <h2 className="text-xl font-semibold">{academy.title}</h2>
            <ul className="mt-2 space-y-2 text-sm">
              {academy.paths.map((path) => (
                <li key={path.slug}>
                  <span className="font-semibold">{path.title}</span>
                  <span> · {path.courses.map((course) => course.title).join(", ")}</span>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
      <form className="mt-8 max-w-xl space-y-3" onSubmit={onSubmit}>
        <h2 className="text-xl font-semibold">New topic page</h2>
        <label className="block text-sm">
          Lesson slug
          <input className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 dark:border-slate-600 dark:bg-slate-950" value={lesson} onChange={(event) => setLesson(event.target.value)} required />
        </label>
        <label className="block text-sm">
          Title
          <input className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 dark:border-slate-600 dark:bg-slate-950" value={title} onChange={(event) => setTitle(event.target.value)} required />
        </label>
        <label className="block text-sm">
          Kind
          <select className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 dark:border-slate-600 dark:bg-slate-950" value={kind} onChange={(event) => setKind(event.target.value)}>
            <option value="reading">Reading</option>
            <option value="video">Video</option>
            <option value="exercise">Interactive exercise</option>
            <option value="knowledge_check">Knowledge check</option>
            <option value="summary">Summary</option>
          </select>
        </label>
        {kind === "video" || kind === "exercise" ? (
          <label className="block text-sm">
            Catalog URL
            <input
              className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 dark:border-slate-600 dark:bg-slate-950"
              value={assetUrl}
              onChange={(event) => setAssetUrl(event.target.value)}
              placeholder="https:// — stored once in the resource catalog"
            />
          </label>
        ) : null}
        <label className="block text-sm">
          Body
          <textarea className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 dark:border-slate-600 dark:bg-slate-950" rows={6} value={body} onChange={(event) => setBody(event.target.value)} />
        </label>
        <button className="rounded-full bg-[#1d4ed8] px-4 py-2 font-semibold text-white" type="submit" disabled={add.isPending}>
          Add page
        </button>
        {notice ? <p className="text-sm">{notice}</p> : null}
        {add.error ? <p className="text-sm">Could not add that page.</p> : null}
      </form>
      <p className="mt-6 text-sm">
        Preview the worked example:{" "}
        <a className="underline" href={`${learner}/learn/what-is-a-state/introduction`}>
          What is a State?
        </a>
      </p>
    </div>
  );
}
