"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { use, useState } from "react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { useStudio } from "@/stores/studio";

type Question = { id: string; kind: string; prompt: string; options: string[] };
type Assessment = {
  id: string;
  title: string;
  scope: string;
  pass_score: number;
  xp_reward: number;
  passed: boolean;
  best_score: number | null;
  questions: Question[];
};
type Result = { question_id: string; correct: boolean; explanation: string };

export default function AssessmentPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const devUserId = useStudio((state) => state.devUserId);
  const client = useQueryClient();
  const query = useQuery({
    queryKey: ["assessment", id, devUserId],
    queryFn: () => api<Assessment>(`/api/v1/learn/assessments/${id}`),
  });
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [results, setResults] = useState<Result[] | null>(null);
  const [summary, setSummary] = useState("");
  const grade = useMutation({
    mutationFn: (assessment: Assessment) =>
      api<{ passed: boolean; score: number; results: Result[]; xp: number }>(`/api/v1/learn/assessments/${assessment.id}`, {
        method: "POST",
        body: JSON.stringify({
          answers: assessment.questions.map((question) => ({
            question_id: question.id,
            response: answers[question.id] || "",
          })),
        }),
      }),
    onSuccess: (result) => {
      setResults(result.results);
      setSummary(
        result.passed
          ? `Passed at ${result.score}%.${result.xp ? ` +${result.xp} XP.` : ""}`
          : `Scored ${result.score}%. The pass mark was not met.`,
      );
      client.invalidateQueries({ queryKey: ["assessment", id] });
    },
  });
  if (query.isLoading) return <p>Loading the assessment…</p>;
  if (!query.data) return <p>That assessment was not found.</p>;
  const assessment = query.data;
  return (
    <form
      className="mx-auto max-w-3xl"
      onSubmit={(event) => {
        event.preventDefault();
        grade.mutate(assessment);
      }}
    >
      <p className="text-sm font-semibold uppercase tracking-wide text-[#1d4ed8]">{assessment.scope} assessment</p>
      <h1 className="mt-2 font-display text-4xl tracking-tight">{assessment.title}</h1>
      <p className="mt-2 text-slate-700 dark:text-slate-300">
        Pass mark {assessment.pass_score}%. {assessment.xp_reward} XP on the first pass.
        {assessment.passed ? ` Best score ${assessment.best_score}%.` : ""}
      </p>
      <div className="mt-6 space-y-4">
        {assessment.questions.map((question) => (
          <fieldset key={question.id} className="rounded-3xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900">
            <legend className="font-semibold">{question.prompt}</legend>
            <div className="mt-3 space-y-2">
              {question.options.map((option) => {
                const value = option.slice(0, 1).toLowerCase();
                return (
                  <label key={option} className="flex gap-2">
                    <input
                      type="radio"
                      name={question.id}
                      checked={answers[question.id] === value}
                      onChange={() => setAnswers({ ...answers, [question.id]: value })}
                    />
                    <span>{option}</span>
                  </label>
                );
              })}
            </div>
            {results?.find((item) => item.question_id === question.id) ? (
              <p className="mt-3 text-sm">
                {results.find((item) => item.question_id === question.id)?.correct ? "Correct. " : "Not yet. "}
                {results.find((item) => item.question_id === question.id)?.explanation}
              </p>
            ) : null}
          </fieldset>
        ))}
      </div>
      {summary ? <p className="mt-4" role="status">{summary}</p> : null}
      <Button className="mt-6" type="submit" disabled={grade.isPending}>Submit assessment</Button>
    </form>
  );
}
