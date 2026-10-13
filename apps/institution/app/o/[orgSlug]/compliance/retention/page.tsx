"use client";

import { QueuePage } from "@/components/queue-page";

export default function Page() {
  return (
    <QueuePage
      title="Retention"
      description="How long membership and grade records are kept."
      empty="Default retention follows the platform policy until an organisation override exists."
    />
  );
}
