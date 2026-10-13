"use client";

import { QueuePage } from "@/components/queue-page";

export default function Page() {
  return (
    <QueuePage
      title="Seats"
      description="Who occupies a licensed seat."
      empty="No seats assigned."
    />
  );
}
