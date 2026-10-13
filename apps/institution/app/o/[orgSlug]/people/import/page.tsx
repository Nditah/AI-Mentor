"use client";

import { QueuePage } from "@/components/queue-page";

export default function Page() {
  return (
    <QueuePage
      title="Import people"
      description="Bulk membership import."
      empty="Import is waiting on the organisation membership API."
    />
  );
}
