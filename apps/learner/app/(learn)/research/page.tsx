"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

type Upload = { id: string; title: string; chunks: number };
type Analysis = {
  mode: string;
  summary: string;
  excerpts: { citation: string; text: string }[];
  equations: string[];
  critique: string | null;
  gaps: string | null;
  future_work: string | null;
  limitations_of_this_pass: string | null;
};

export default function ResearchPage() {
  const client = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [question, setQuestion] = useState("What claim does this document actually make?");
  const [documentId, setDocumentId] = useState<string | null>(null);
  const upload = useMutation({
    mutationFn: async () => {
      const body = new FormData();
      if (!file) throw new Error("Choose a file.");
      body.append("file", file);
      return api<Upload>("/api/v1/research/documents", { method: "POST", body });
    },
    onSuccess: (result) => setDocumentId(result.id),
  });
  const analyze = useMutation({
    mutationFn: () =>
      api<Analysis>("/api/v1/research/analyze", {
        method: "POST",
        body: JSON.stringify({ document_id: documentId, question }),
      }),
    onSuccess: () => client.invalidateQueries({ queryKey: ["dashboard"] }),
  });

  function onUpload(event: FormEvent) {
    event.preventDefault();
    upload.mutate();
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <section>
        <h1 className="font-display text-4xl tracking-tight">Research</h1>
        <p className="mt-2 text-slate-700 dark:text-slate-300">
          PDF, DOCX, Markdown, or text. Scanned pages are not read. A critique is shown only when it cites an excerpt.
        </p>
        <form className="mt-4 space-y-3" onSubmit={onUpload}>
          <label className="block text-sm font-semibold" htmlFor="paper">
            Document
          </label>
          <input
            id="paper"
            type="file"
            accept=".pdf,.docx,.md,.txt,application/pdf,text/markdown,text/plain"
            onChange={(event) => setFile(event.target.files?.[0] || null)}
          />
          <Button type="submit" disabled={!file || upload.isPending}>
            Upload
          </Button>
          {upload.data ? <p className="text-sm">{upload.data.chunks} chunks stored from {upload.data.title}.</p> : null}
          {upload.error ? <p className="text-sm text-red-800 dark:text-red-300">{upload.error.message}</p> : null}
        </form>
        <form
          className="mt-6 space-y-3"
          onSubmit={(event) => {
            event.preventDefault();
            analyze.mutate();
          }}
        >
          <label className="block text-sm font-semibold" htmlFor="question">
            Question
          </label>
          <textarea
            id="question"
            className="min-h-28 w-full rounded-2xl border border-slate-300 bg-white p-3 dark:border-slate-600 dark:bg-slate-950"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
          />
          <Button type="submit" disabled={!documentId || analyze.isPending}>
            Analyze
          </Button>
        </form>
      </section>
      <section aria-live="polite" className="space-y-4">
        {analyze.data ? (
          <>
            <p className="text-sm font-semibold uppercase tracking-wide text-[#1d4ed8]">{analyze.data.mode} pass</p>
            <h2 className="text-2xl font-semibold">Summary</h2>
            <p className="whitespace-pre-wrap">{analyze.data.summary}</p>
            <h2 className="text-xl font-semibold">Excerpts</h2>
            <ul className="space-y-2">
              {analyze.data.excerpts.map((excerpt) => (
                <li key={excerpt.citation} className="rounded-2xl bg-white p-3 dark:bg-slate-900">
                  <p className="font-semibold">{excerpt.citation}</p>
                  <p className="text-sm">{excerpt.text}</p>
                </li>
              ))}
            </ul>
            <Field label="Equations" value={analyze.data.equations.join("\n") || "None found."} />
            <Field label="Critique" value={analyze.data.critique || "Withheld."} />
            <Field label="Gaps" value={analyze.data.gaps || "Withheld."} />
            <Field label="Future work" value={analyze.data.future_work || "Withheld."} />
            {analyze.data.limitations_of_this_pass ? <p className="text-sm text-slate-600 dark:text-slate-300">{analyze.data.limitations_of_this_pass}</p> : null}
          </>
        ) : (
          <p className="text-slate-600 dark:text-slate-300">Upload a document, then ask a question about that file.</p>
        )}
        {analyze.error ? <p className="text-red-800 dark:text-red-300">{analyze.error.message}</p> : null}
      </section>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <h2 className="text-xl font-semibold">{label}</h2>
      <p className="whitespace-pre-wrap">{value}</p>
    </div>
  );
}
