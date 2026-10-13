"use client";

import { QueuePage } from "@/components/queue-page";

export default function Page() {
  return (
    <QueuePage
      title="Organisation structure"
      description="Campuses and departments (at most two levels)."
      empty="This organisation has no units yet. Add a campus or department to group cohorts."
    />
  );
}
