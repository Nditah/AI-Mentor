"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useMemo, useState } from "react";
import { api } from "@/lib/api";
import { useStudio } from "@/stores/studio";

type Faculty = { slug: string; title: string; summary: string };
type Level = { slug: string; title: string };
type AcademyFilter = {
  slug: string;
  title: string;
  summary: string;
  faculty: string;
  yours?: boolean;
};
type Program = {
  slug: string;
  title: string;
  description: string;
  level: string;
  faculty: Faculty;
  academy: { slug: string; title: string; faculty: string };
  progress: number;
  locked: boolean;
  yours?: boolean;
  courses: number;
  remaining_lessons?: number;
  href: string | null;
  cue?: string;
};
type World = {
  filters: { faculties: Faculty[]; levels: Level[]; academies: AcademyFilter[] };
  programs: Program[];
};

function Chip({
  pressed,
  onClick,
  children,
}: {
  pressed: boolean;
  onClick: () => void;
  children: string;
}) {
  return (
    <button
      type="button"
      aria-pressed={pressed}
      onClick={onClick}
      className={
        pressed
          ? "rounded-full bg-[#1d4ed8] px-3 py-1.5 text-sm font-semibold text-white"
          : "rounded-full border border-slate-300 bg-white px-3 py-1.5 text-sm font-semibold text-slate-800 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
      }
    >
      {children}
    </button>
  );
}

export default function AcademiesPage() {
  const devUserId = useStudio((state) => state.devUserId);
  const query = useQuery({
    queryKey: ["world", devUserId],
    queryFn: () => api<World>("/api/v1/learn/world"),
  });
  const [faculty, setFaculty] = useState("");
  const [level, setLevel] = useState("");
  const [academy, setAcademy] = useState("");

  const filters = query.data?.filters;
  const academyOptions = useMemo(() => {
    const rows = filters?.academies || [];
    if (!faculty) return rows;
    return rows.filter((item) => item.faculty === faculty);
  }, [filters, faculty]);

  const programs = useMemo(() => {
    return (query.data?.programs || []).filter((item) => {
      if (faculty && item.faculty.slug !== faculty) return false;
      if (level && item.level !== level) return false;
      if (academy && item.academy.slug !== academy) return false;
      return true;
    });
  }, [query.data, faculty, level, academy]);

  return (
    <div>
      <h1 className="font-display text-4xl tracking-tight">Learning world</h1>
      <p className="mt-2 max-w-2xl text-slate-700 dark:text-slate-300">
        Every learning path is on this page. Faculty and level narrow the list. Academies are
        filters, not another click before you can start.
      </p>
      {query.isLoading ? <p className="mt-6">Loading the world…</p> : null}
      {query.error ? <p className="mt-6">Learning paths are unavailable.</p> : null}
      {filters ? (
        <div className="mt-6 space-y-4">
          <fieldset>
            <legend className="text-sm font-semibold">Faculty</legend>
            <div className="mt-2 flex flex-wrap gap-2">
              <Chip pressed={faculty === ""} onClick={() => { setFaculty(""); setAcademy(""); }}>
                All
              </Chip>
              {filters.faculties.map((item) => (
                <Chip
                  key={item.slug}
                  pressed={faculty === item.slug}
                  onClick={() => {
                    setFaculty(item.slug);
                    setAcademy("");
                  }}
                >
                  {item.title}
                </Chip>
              ))}
            </div>
          </fieldset>
          <fieldset>
            <legend className="text-sm font-semibold">Level</legend>
            <div className="mt-2 flex flex-wrap gap-2">
              <Chip pressed={level === ""} onClick={() => setLevel("")}>
                All
              </Chip>
              {filters.levels.map((item) => (
                <Chip
                  key={item.slug}
                  pressed={level === item.slug}
                  onClick={() => setLevel(item.slug)}
                >
                  {item.title}
                </Chip>
              ))}
            </div>
          </fieldset>
          <fieldset>
            <legend className="text-sm font-semibold">Academy</legend>
            <div className="mt-2 flex flex-wrap gap-2">
              <Chip pressed={academy === ""} onClick={() => setAcademy("")}>
                All
              </Chip>
              {academyOptions.map((item) => (
                <Chip
                  key={item.slug}
                  pressed={academy === item.slug}
                  onClick={() => {
                    setAcademy(item.slug);
                    setFaculty(item.faculty);
                  }}
                >
                  {item.title.replace(/ Academy$/, "")}
                </Chip>
              ))}
            </div>
          </fieldset>
        </div>
      ) : null}
      <div className="mt-6 grid gap-4 md:grid-cols-2">
        {programs.map((item) => (
          <article
            key={item.slug}
            className="rounded-3xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900"
          >
            <p className="text-xs font-semibold uppercase tracking-wide text-[#1d4ed8]">
              {item.faculty.title}
              {" · "}
              {item.level}
              {item.yours ? " · Your goal" : ""}
            </p>
            <p className="mt-1 text-sm font-semibold">{item.progress}% complete</p>
            <h2 className="mt-1 text-2xl font-semibold">
              {item.href ? (
                <Link className="underline" href={item.href}>
                  {item.title}
                </Link>
              ) : (
                item.title
              )}
            </h2>
            <p className="mt-2 text-slate-700 dark:text-slate-300">{item.description}</p>
            <p className="mt-3 text-sm">
              {item.academy.title}
              {item.courses
                ? ` · ${item.courses} course${item.courses === 1 ? "" : "s"}`
                : ""}
              {item.remaining_lessons != null
                ? ` · ${item.remaining_lessons} lesson${item.remaining_lessons === 1 ? "" : "s"} remaining`
                : ""}
            </p>
            {item.locked ? (
              <p className="mt-2 text-sm">Finish the previous path in this academy to open this one.</p>
            ) : null}
            {item.cue ? <p className="mt-2 text-sm font-semibold">{item.cue}</p> : null}
          </article>
        ))}
      </div>
      {query.data && programs.length === 0 ? (
        <p className="mt-6 text-slate-700 dark:text-slate-300">No paths match those filters.</p>
      ) : null}
    </div>
  );
}
