"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { MentorMarkdown } from "@/components/markdown-view";
import { Button } from "@/components/ui/button";
import { api, apiStream, ApiError, readSse } from "@/lib/api";
import { useStudio } from "@/stores/studio";

type Prefs = {
  tutor_mode: "socratic" | "direct";
  learning_style: string;
  maths_comfort: string | null;
  programming_experience: string | null;
  weekly_minutes: number | null;
};

type Turn = { role: "user" | "assistant"; content: string };

export default function TutorPage() {
  const client = useQueryClient();
  const notes = useStudio((state) => state.notes);
  const setNotes = useStudio((state) => state.setNotes);
  const devUserId = useStudio((state) => state.devUserId);
  const prefs = useQuery({
    queryKey: ["prefs", devUserId],
    queryFn: () => api<Prefs>("/api/v1/me/learning-preferences"),
  });
  const [mode, setMode] = useState<"socratic" | "direct">("socratic");
  useEffect(() => {
    if (prefs.data?.tutor_mode) setMode(prefs.data.tutor_mode);
  }, [prefs.data]);
  const saveMode = useMutation({
    mutationFn: (next: "socratic" | "direct") =>
      api("/api/v1/me/learning-preferences", {
        method: "PATCH",
        body: JSON.stringify({ tutor_mode: next }),
      }),
  });
  const [draft, setDraft] = useState("Teach me Reinforcement Learning");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function sendMessage(message: string) {
    setPending(true);
    setError(null);
    setTurns((current) => [...current, { role: "user", content: message }, { role: "assistant", content: "" }]);
    setDraft("");
    try {
      const response = await apiStream("/api/v1/chat/stream", {
        method: "POST",
        body: JSON.stringify({ message, mode, conversation_id: conversationId }),
      });
      let assembled = "";
      for await (const event of readSse(response)) {
        if (event.type === "error") {
          throw new ApiError(Number(event.status) || 400, String(event.detail || "The tutor could not answer."));
        }
        if (event.type === "meta" && typeof event.conversation_id === "string") {
          setConversationId(event.conversation_id);
        }
        if (event.type === "delta" && typeof event.text === "string") {
          assembled += event.text;
          const snapshot = assembled;
          setTurns((current) => {
            const next = [...current];
            next[next.length - 1] = { role: "assistant", content: snapshot };
            return next;
          });
        }
        if (event.type === "done") {
          const reply = event.reply as { content?: string } | undefined;
          if (reply?.content) {
            assembled = reply.content;
            setTurns((current) => {
              const next = [...current];
              next[next.length - 1] = { role: "assistant", content: assembled };
              return next;
            });
          }
          if (typeof event.conversation_id === "string") setConversationId(event.conversation_id);
        }
      }
      client.invalidateQueries({ queryKey: ["dashboard"] });
    } catch (caught) {
      setTurns((current) => current.slice(0, -2));
      setDraft(message);
      setError(caught instanceof ApiError ? caught.message : "The tutor could not answer.");
    } finally {
      setPending(false);
    }
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!draft.trim() || pending) return;
    void sendMessage(draft.trim());
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_280px]">
      <section>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="font-display text-4xl tracking-tight">Tutor</h1>
          <fieldset className="flex gap-2">
            <legend className="sr-only">Tutor mode</legend>
            {(["socratic", "direct"] as const).map((value) => (
              <label key={value} className="text-sm font-semibold">
                <input
                  className="mr-1"
                  type="radio"
                  name="mode"
                  checked={mode === value}
                  onChange={() => {
                    setMode(value);
                    saveMode.mutate(value);
                  }}
                />
                {value === "socratic" ? "Socratic" : "Direct"}
              </label>
            ))}
          </fieldset>
        </div>
        <div className="mt-4 min-h-80 space-y-3" role="log" aria-live="polite" aria-relevant="additions">
          {turns.length === 0 ? (
            <p className="text-slate-600 dark:text-slate-300">Ask for a concept. In Socratic mode the first reply is a question.</p>
          ) : null}
          {turns.map((turn, index) => (
            <article
              key={`${turn.role}-${index}`}
              className={
                turn.role === "assistant"
                  ? "rounded-3xl bg-white p-4 shadow-card dark:bg-slate-900"
                  : "rounded-3xl bg-slate-100 p-4 dark:bg-slate-800"
              }
            >
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{turn.role}</p>
              {turn.content ? <MentorMarkdown content={turn.content} /> : <p className="mt-1 text-slate-500">Thinking…</p>}
            </article>
          ))}
        </div>
        <form className="mt-4 flex flex-col gap-3" onSubmit={onSubmit}>
          <label className="text-sm font-semibold" htmlFor="tutor-message">
            Message
          </label>
          <textarea
            id="tutor-message"
            className="min-h-28 rounded-2xl border border-slate-300 bg-white p-3 dark:border-slate-600 dark:bg-slate-950"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) onSubmit(event);
            }}
          />
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm text-slate-500">Press Command Enter to send.</p>
            <Button type="submit" disabled={pending}>
              {pending ? "Thinking" : "Send"}
            </Button>
          </div>
          {error ? <p className="text-sm text-red-800 dark:text-red-300">{error}</p> : null}
        </form>
      </section>
      <aside className="space-y-4">
        <section className="rounded-3xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
          <h2 className="font-semibold">Notes</h2>
          <label className="sr-only" htmlFor="notes">
            Personal notes
          </label>
          <textarea
            id="notes"
            className="mt-2 min-h-40 w-full rounded-2xl border border-slate-300 bg-transparent p-3 dark:border-slate-600"
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
          />
          <p className="mt-2 text-xs text-slate-500">Notes stay in this browser.</p>
        </section>
        <section className="rounded-3xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
          <h2 className="font-semibold">Teaching for you</h2>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
            {prefs.data
              ? `${prefs.data.learning_style.replace("_", "-")} · ${prefs.data.maths_comfort || "maths unset"} · ${prefs.data.programming_experience || "programming unset"}${prefs.data.weekly_minutes ? ` · ${prefs.data.weekly_minutes} min/week` : ""}`
              : "Load settings to adapt examples, maths, and session length."}
          </p>
          <p className="mt-2 text-sm">
            <Link className="font-semibold text-[#1d4ed8] underline" href="/settings">
              Change in Settings
            </Link>
          </p>
        </section>
        <section className="rounded-3xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
          <h2 className="font-semibold">Resources</h2>
          <ul className="mt-2 space-y-1 text-sm">
            <li><a className="underline" href="/paths/reinforcement-learning">Reinforcement learning track</a></li>
            <li><a className="underline" href="/lab">Coding lab</a></li>
            <li><a className="underline" href="/graph">Concept map</a></li>
          </ul>
        </section>
      </aside>
    </div>
  );
}
