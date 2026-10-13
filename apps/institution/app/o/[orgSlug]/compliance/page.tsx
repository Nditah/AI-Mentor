"use client";

import { QueuePage } from "@/components/queue-page";

export default function Page() {
  return (
    <QueuePage
      title="Compliance"
      description="Data requests, retention, consent, and the organisation audit log."
      empty="Open a data request from the list when a learner or regulator asks."
    />
  );
}
