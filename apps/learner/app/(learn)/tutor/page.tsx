"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { MentorMarkdown } from "@/components/markdown-view";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { ChatReply } from "@/lib/types";
import { useStudio } from "@/stores/studio";

type Turn = { role: "user" | "assistant"; content: string };

export default function TutorPage() {
  const client = useQueryClient();
  const notes = useStudio((state) => state.notes);
  const setNotes = useStudio((state) => state.setNotes);
  const [mode, setMode] = useState<"socratic" | "direct">("socratic");
  const [draft, setDraft] = useState("Teach me Reinforcement Learning");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [turns, setTurns] = useState<Turn[]>([]);
  const send = useMutation({
    mutationFn: (message: string) =>
      api<ChatReply>("/api/v1/chat", {
        method: "POST",
        body: JSON.stringify({ message, mode, conversation_id: conversationId }),
      }),
    onSuccess: (result, message) => {
      client.invalidateQueries({ queryKey: ["dashboard"] });
      setConversationId(result.conversation_id);
      setTurns((current) => [...current, { role: "user", content: message }, { role: "assistant", content: result.reply.content }]);
      setDraft("");
    },
  });

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!draft.trim()) return;
    send.mutate(draft.trim());
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
                  onChange={() => setMode(value)}
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
              <MentorMarkdown content={turn.content} />
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
            <Button type="submit" disabled={send.isPending}>
              {send.isPending ? "Thinking" : "Send"}
            </Button>
          </div>
          {send.error ? <p className="text-sm text-red-800 dark:text-red-300">{send.error.message}</p> : null}
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
