"use client";

import { QueuePage } from "@/components/queue-page";

export default function Page() {
  return (
    <QueuePage
      title="Instructors"
      description="Staff with a teaching assignment."
      empty="No instructors assigned."
    />
  );
}
