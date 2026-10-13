"use client";

import { QueuePage } from "@/components/queue-page";

export default function Page() {
  return (
    <QueuePage
      title="Invoices"
      description="Organisation billing history."
      empty="No invoices."
    />
  );
}
