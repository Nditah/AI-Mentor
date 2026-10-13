"use client";

import { QueuePage } from "@/components/queue-page";

export default function Page() {
  return (
    <QueuePage
      title="Learners"
      description="People enrolled in your cohorts."
      empty="No learners in this organisation yet. Import a roster or send invites."
    />
  );
}
