"use client";

import { QueuePage } from "@/components/queue-page";

export default function Page() {
  return (
    <QueuePage
      title="Organisation audit log"
      description="Actions in this tenant."
      empty="The platform audit log stays in the Admin App. This view lists organisation-scoped events once tenancy is on."
    />
  );
}
