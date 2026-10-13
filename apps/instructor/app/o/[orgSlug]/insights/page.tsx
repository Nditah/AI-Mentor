"use client";

import { QueuePage } from "@/components/queue-page";

export default function Page() {
  return (
    <QueuePage
      title="Insights"
      description="Cross-cohort progress, risk, and attendance."
      empty="Insights use organisation analytics once tenancy is on. Platform-wide counts stay in the Admin App."
    />
  );
}
