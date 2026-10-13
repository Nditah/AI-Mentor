"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { api } from "@/lib/api";

const kinds = ["lesson", "notes", "paper", "quiz", "guide", "code", "link", "dataset"];
const levels = ["beginner", "intermediate", "advanced", "expert", "phd"];

export default function NewAssetPage() {
  const router = useRouter();
  const client = useQueryClient();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [topic, setTopic] = useState("reinforcement-learning");
  const [kind, setKind] = useState("notes");
  const [difficulty, setDifficulty] = useState("intermediate");
  const [minutes, setMinutes] = useState(30);
  const [tags, setTags] = useState("");
  const [body, setBody] = useState("");
  const save = useMutation({
    mutationFn: () =>
      api<{ id: string }>("/api/v1/admin/assets", {
        method: "POST",
        body: JSON.stringify({
          title,
          description,
          topic,
          kind,
          difficulty,
          estimated_minutes: minutes,
          tags: tags.split(",").map((tag) => tag.trim()).filter(Boolean),
          body_md: body,
        }),
      }),
    onSuccess: (asset) => {
      client.invalidateQueries({ queryKey: ["assets"] });
      router.push(`/library/${asset.id}`);
    },
  });

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    save.mutate();
  }

  return (
    <form className="max-w-2xl space-y-4" onSubmit={onSubmit}>
      <h1 className="text-3xl font-semibold tracking-tight">Add resource</h1>
      <p className="text-slate-600 dark:text-slate-300">This creates a draft. It is not visible to students.</p>
      <Field label="Title" value={title} onChange={setTitle} />
      <label className="block text-sm font-semibold">
        Description
        <textarea className="mt-1 w-full rounded-2xl border border-slate-300 bg-white p-3 dark:border-slate-600 dark:bg-slate-950" value={description} onChange={(event) => setDescription(event.target.value)} required minLength={20} />
      </label>
      <div className="grid gap-3 sm:grid-cols-2">
        <Select label="Type" value={kind} options={kinds} onChange={setKind} />
        <Select label="Difficulty" value={difficulty} options={levels} onChange={setDifficulty} />
      </div>
      <Field label="Topic" value={topic} onChange={setTopic} />
      <label className="block text-sm font-semibold">
        Study time in minutes
        <input className="mt-1 w-full rounded-full border border-slate-300 bg-white px-3 py-2 dark:border-slate-600 dark:bg-slate-950" type="number" min={1} max={600} value={minutes} onChange={(event) => setMinutes(Number(event.target.value))} />
      </label>
      <Field label="Tags, comma separated" value={tags} onChange={setTags} />
      <label className="block text-sm font-semibold">
        Body
        <textarea className="mt-1 min-h-40 w-full rounded-2xl border border-slate-300 bg-white p-3 font-mono text-sm dark:border-slate-600 dark:bg-slate-950" value={body} onChange={(event) => setBody(event.target.value)} />
      </label>
      <button className="rounded-full bg-[#1d4ed8] px-4 py-2 font-semibold text-white" type="submit" disabled={save.isPending}>
        Save draft
      </button>
      {save.error ? <p className="text-red-800 dark:text-red-300">{save.error.message}</p> : null}
    </form>
  );
}

function Field({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <label className="block text-sm font-semibold">
      {label}
      <input className="mt-1 w-full rounded-full border border-slate-300 bg-white px-3 py-2 dark:border-slate-600 dark:bg-slate-950" value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

function Select({ label, value, options, onChange }: { label: string; value: string; options: string[]; onChange: (value: string) => void }) {
  return (
    <label className="block text-sm font-semibold">
      {label}
      <select className="mt-1 w-full rounded-full border border-slate-300 bg-white px-3 py-2 dark:border-slate-600 dark:bg-slate-950" value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => (
          <option key={option}>{option}</option>
        ))}
      </select>
    </label>
  );
}
