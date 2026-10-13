"use client";

import { QueuePage } from "@/components/queue-page";

export default function Page() {
  return (
    <QueuePage
      title="Cohorts"
      description="Classes you teach in this organisation."
      empty="No cohorts yet. Create a cohort to pin a learning-path release and invite learners."
    />
  );
}
