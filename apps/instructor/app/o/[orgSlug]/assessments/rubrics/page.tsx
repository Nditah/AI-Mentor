"use client";

import { QueuePage } from "@/components/queue-page";

export default function Page() {
  return (
    <QueuePage
      title="Rubrics"
      description="Shared marking criteria for written work."
      empty="No rubrics yet."
    />
  );
}
