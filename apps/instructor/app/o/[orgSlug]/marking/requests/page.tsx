"use client";

import { QueuePage } from "@/components/queue-page";

export default function Page() {
  return (
    <QueuePage
      title="Grade review requests"
      description="Learners asking for a mark to be looked at again."
      empty="No review requests."
    />
  );
}
