"use client";

import { AppLauncher } from "@/components/app-launcher";

export default function AppsPage() {
  return (
    <div>
      <h1 className="font-display text-4xl tracking-tight">Applications</h1>
      <p className="mt-2 max-w-xl text-slate-700 dark:text-slate-300">
        Teaching, organisation administration, platform operations, and content authoring each have
        their own app on the same API. The launcher lists only the apps your role may open.
      </p>
      <AppLauncher current="learner" />
    </div>
  );
}
