"use client";

import { QueuePage } from "@/components/queue-page";

export default function Page() {
  return (
    <QueuePage
      title="Data requests"
      description="DSARs for people in this organisation."
      empty="No data requests."
    />
  );
}
