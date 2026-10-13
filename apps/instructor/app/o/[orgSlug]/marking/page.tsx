"use client";

import { QueuePage } from "@/components/queue-page";

export default function Page() {
  return (
    <QueuePage
      title="Marking queue"
      description="Submissions waiting across your cohorts."
      empty="The marking queue is empty. Assignments appear here after learners submit."
    />
  );
}
