"use client";

import { QueuePage } from "@/components/queue-page";

export default function Page() {
  return (
    <QueuePage
      title="Import learners"
      description="Upload a roster for this organisation."
      empty="Roster import is waiting on the organisation membership API. Files are not uploaded from this screen yet."
    />
  );
}
