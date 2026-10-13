"use client";

import { QueuePage } from "@/components/queue-page";

export default function Page() {
  return (
    <QueuePage
      title="Messages"
      description="Announcements and threads for your cohorts."
      empty="No announcements yet."
    />
  );
}
