"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

type Question = { id: string; kind: string; prompt: string; options: string[]; position: number };
type Quiz = {
  id: string;
  title: string;
  difficulty_note: string | null;
  coach_note: string | null;
  questions: Question[];
};
type Grade = {
  score: number;
  max_score: number;
  results: { question_id: string; correct: boolean; feedback: string; explanation: string }[];
};

export default function QuizPage() {
  const client = useQueryClient();
  const [concept, setConcept] = useState("agent-environment");
  const [difficulty, setDifficulty] = useState("beginner");
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const generate = useMutation({
    mutationFn: () =>
      api<Quiz>("/api/v1/quiz/generate", {
        method: "POST",
        body: JSON.stringify({ concept_slug: concept, difficulty }),
      }),
    onSuccess: () => setAnswers({}),
  });
  const grade = useMutation({
    mutationFn: () =>
      api<Grade>(`/api/v1/quiz/${generate.data?.id}/grade`, {
        method: "POST",
        body: JSON.stringify({
          answers: Object.entries(answers).map(([question_id, response]) => ({ question_id, response })),
        }),
      }),
    onSuccess: () => client.invalidateQueries({ queryKey: ["dashboard"] }),
  });

  function onGenerate(event: FormEvent) {
    event.preventDefault();
    grade.reset();
    generate.mutate();
  }

  const quiz = generate.data;
  const feedback = new Map(grade.data?.results.map((item) => [item.question_id, item]) || []);

  return (
    <div className="max-w-3xl">
      <h1 className="font-display text-4xl tracking-tight">Quiz</h1>
      <p className="mt-2 text-slate-700 dark:text-slate-300">
        Items come from authored templates. The answer key is graded on the server and is not sent with the quiz.
      </p>
      <form className="mt-4 flex flex-wrap items-end gap-3" onSubmit={onGenerate}>
        <label className="text-sm font-semibold">
          Concept slug
          <input
            className="mt-1 block rounded-full border border-slate-300 bg-white px-3 py-2 dark:border-slate-600 dark:bg-slate-950"
            value={concept}
            onChange={(event) => setConcept(event.target.value)}
          />
        </label>
        <label className="text-sm font-semibold">
          Difficulty
          <select
            className="mt-1 block rounded-full border border-slate-300 bg-white px-3 py-2 dark:border-slate-600 dark:bg-slate-950"
            value={difficulty}
            onChange={(event) => setDifficulty(event.target.value)}
          >
            {["beginner", "intermediate", "advanced", "expert", "phd"].map((level) => (
              <option key={level} value={level}>
                {level}
              </option>
            ))}
          </select>
        </label>
        <Button type="submit" disabled={generate.isPending}>
          Generate
        </Button>
      </form>
      {generate.error ? <p className="mt-3 text-red-800 dark:text-red-300">{generate.error.message}</p> : null}
      {quiz ? (
        <form
          className="mt-6 space-y-5"
          onSubmit={(event) => {
            event.preventDefault();
            grade.mutate();
          }}
        >
          <h2 className="text-2xl font-semibold">{quiz.title}</h2>
          {quiz.difficulty_note ? <p className="text-sm">{quiz.difficulty_note}</p> : null}
          {quiz.coach_note ? <p className="text-sm text-slate-600 dark:text-slate-300">{quiz.coach_note}</p> : null}
          {quiz.questions.map((question, index) => {
            const result = feedback.get(question.id);
            return (
              <fieldset key={question.id} className="rounded-3xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
                <legend className="px-1 font-semibold">
                  {index + 1}. {question.prompt}
                </legend>
                {question.options.length ? (
                  <div className="mt-3 space-y-2">
                    {question.options.map((option, optionIndex) => {
                      const letter = String.fromCharCode(65 + optionIndex);
                      return (
                        <label key={option} className="flex gap-2 text-sm">
                          <input
                            type="radio"
                            name={question.id}
                            value={letter}
                            checked={answers[question.id] === letter}
                            onChange={() => setAnswers((current) => ({ ...current, [question.id]: letter }))}
                          />
                          <span>
                            {letter}. {option}
                          </span>
                        </label>
                      );
                    })}
                  </div>
                ) : (
                  <textarea
                    className="mt-3 min-h-24 w-full rounded-2xl border border-slate-300 bg-transparent p-3 dark:border-slate-600"
                    value={answers[question.id] || ""}
                    onChange={(event) => setAnswers((current) => ({ ...current, [question.id]: event.target.value }))}
                  />
                )}
                {result ? (
                  <p className="mt-3 text-sm">
                    {result.correct ? "Correct." : "Not yet."} {result.feedback} {result.explanation}
                  </p>
                ) : null}
              </fieldset>
            );
          })}
          <Button type="submit" disabled={grade.isPending || Object.keys(answers).length === 0}>
            Grade
          </Button>
          {grade.data ? (
            <p className="font-semibold">
              Score {grade.data.score} of {grade.data.max_score}
            </p>
          ) : null}
          {grade.error ? <p className="text-red-800 dark:text-red-300">{grade.error.message}</p> : null}
        </form>
      ) : null}
    </div>
  );
}
