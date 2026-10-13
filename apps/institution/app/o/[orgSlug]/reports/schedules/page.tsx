"use client";

import { QueuePage } from "@/components/queue-page";

export default function Page() {
  return (
    <QueuePage
      title="Report schedules"
      description="Email or export a report on a cadence."
      empty="No schedules."
    />
  );
}
