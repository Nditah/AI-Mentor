"use client";

import { QueuePage } from "@/components/queue-page";

export default function Page() {
  return (
    <QueuePage
      title="Invites"
      description="Pending enrolment codes and invite links."
      empty="No pending invites."
    />
  );
}
