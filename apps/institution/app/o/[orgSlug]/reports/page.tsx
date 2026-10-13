"use client";

import { QueuePage } from "@/components/queue-page";

export default function Page() {
  return (
    <QueuePage
      title="Reports"
      description="Saved report definitions for this organisation."
      empty="No reports saved. Workforce and licence reports appear here after the first licence is issued."
    />
  );
}
