"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useEffect } from "react";
import { MentorMarkdown } from "@/components/markdown-view";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { useStudio } from "@/stores/studio";

type Project = { slug: string; title: string; brief_md: string; starter_code: string };
type Run = { status: string; stdout: string; stderr: string; review: string };

export default function LabPage() {
  const client = useQueryClient();
  const code = useStudio((state) => state.labCode);
  const setCode = useStudio((state) => state.setLabCode);
  const projects = useQuery({
    queryKey: ["projects"],
    queryFn: () => api<Project[]>("/api/v1/lab/projects"),
  });
  const project = projects.data?.[0];
  useEffect(() => {
    if (project && code.trim() === "") setCode(project.starter_code);
  }, [project, code, setCode]);
  const run = useMutation({
    mutationFn: () =>
      api<Run>("/api/v1/lab/run", {
        method: "POST",
        body: JSON.stringify({ code, project_slug: project?.slug }),
      }),
    onSuccess: () => client.invalidateQueries({ queryKey: ["dashboard"] }),
  });

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    run.mutate();
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <section>
        <h1 className="font-display text-4xl tracking-tight">Coding lab</h1>
        <p className="mt-2 text-slate-700 dark:text-slate-300">
          Python only. The runner allows a small standard-library set plus GridWorld, then stops the process after three seconds.
        </p>
        {project ? <MentorMarkdown content={project.brief_md} /> : null}
        <form onSubmit={onSubmit}>
          <label className="mt-4 block text-sm font-semibold" htmlFor="code">
            Editor
          </label>
          <textarea
            id="code"
            spellCheck={false}
            className="mt-2 min-h-72 w-full rounded-2xl border border-slate-300 bg-slate-950 p-4 font-mono text-sm text-slate-100"
            value={code}
            onChange={(event) => setCode(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Tab") {
                event.preventDefault();
                const target = event.currentTarget;
                const start = target.selectionStart;
                const next = `${code.slice(0, start)}    ${code.slice(target.selectionEnd)}`;
                setCode(next);
              }
            }}
          />
          <Button className="mt-3" type="submit" disabled={run.isPending}>
            {run.isPending ? "Running" : "Run and review"}
          </Button>
        </form>
      </section>
      <section className="space-y-4" aria-live="polite">
        <h2 className="text-xl font-semibold">Output</h2>
        {run.data ? (
          <>
            <p className="text-sm font-semibold">Status: {run.data.status}</p>
            <pre className="overflow-x-auto rounded-2xl bg-slate-950 p-4 text-sm text-slate-100">{run.data.stdout || "No output."}</pre>
            {run.data.stderr ? <pre className="overflow-x-auto rounded-2xl bg-red-950 p-4 text-sm text-red-100">{run.data.stderr}</pre> : null}
            <div className="rounded-3xl bg-white p-4 dark:bg-slate-900">
              <h3 className="font-semibold">Feedback</h3>
              <MentorMarkdown content={run.data.review} />
            </div>
          </>
        ) : (
          <p className="text-slate-600 dark:text-slate-300">Run the file to see stdout and the review.</p>
        )}
        {run.error ? <p className="text-red-800 dark:text-red-300">{run.error.message}</p> : null}
      </section>
    </div>
  );
}
