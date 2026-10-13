"use client";

import { QueuePage } from "@/components/queue-page";

export default function Page() {
  return (
    <QueuePage
      title="Calendar"
      description="Plan items and live sessions across your cohorts."
      empty="No sessions are scheduled. Pin a path release to a cohort to populate the calendar."
    />
  );
}
