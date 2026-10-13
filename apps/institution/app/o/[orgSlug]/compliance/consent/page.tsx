"use client";

import { QueuePage } from "@/components/queue-page";

export default function Page() {
  return (
    <QueuePage
      title="Consent"
      description="Leaderboard, research, and analytics consent."
      empty="No consent records to review."
    />
  );
}
