"use client";

import { motion, useReducedMotion } from "framer-motion";
import { Button } from "@/components/ui/button";

const lines = [
  ["You", "Teach me reinforcement learning."],
  ["Mentor", "What do you think an agent does in an environment?"],
];

export function Hero() {
  const reduce = useReducedMotion();
  return (
    <section className="mx-auto grid max-w-6xl items-center gap-10 px-5 py-12 lg:grid-cols-[1.1fr_0.9fr]">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#1d4ed8]">Beginner to research</p>
        <h1 className="mt-3 font-display text-5xl leading-tight tracking-tight md:text-6xl">
          A mentor that makes you try before it explains.
        </h1>
        <p className="mt-5 max-w-xl text-lg text-slate-700 dark:text-slate-300">
          AI Mentor teaches machine learning, reinforcement learning, robotics, and research methods. The tutor asks, the lab runs a restricted Python file, and paper notes stay tied to the pages you uploaded.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Button href="/tutor">Start with the tutor</Button>
          <Button href="/paths/reinforcement-learning" variant="quiet">
            Open the RL track
          </Button>
        </div>
      </div>
      <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-card dark:border-slate-700 dark:bg-slate-900" aria-label="Sample tutoring exchange">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Socratic mode</p>
        <ol className="mt-4 space-y-3">
          {lines.map(([who, text], index) => (
            <motion.li
              key={who}
              initial={reduce ? false : { opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: reduce ? 0 : index * 0.15 }}
              className={who === "Mentor" ? "rounded-2xl bg-slate-100 p-4 dark:bg-slate-800" : "p-4"}
            >
              <p className="text-xs font-semibold uppercase tracking-wide text-[#6d28d9]">{who}</p>
              <p className="mt-1">{text}</p>
            </motion.li>
          ))}
        </ol>
      </div>
    </section>
  );
}
