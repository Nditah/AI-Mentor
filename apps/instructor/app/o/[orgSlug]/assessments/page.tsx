"use client";

import { QueuePage } from "@/components/queue-page";

export default function Page() {
  return (
    <QueuePage
      title="Assessments"
      description="Organisation assessment library. Answer keys stay on the server."
      empty="No assessments in this organisation. Create a quiz in Content Studio and assign it here."
    />
  );
}
