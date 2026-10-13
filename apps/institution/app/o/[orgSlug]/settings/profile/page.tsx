"use client";

import { QueuePage } from "@/components/queue-page";

export default function Page() {
  return (
    <QueuePage
      title="Organisation profile"
      description="Name, kind, locale, time zone, and labels."
      empty="Profile edits will call PATCH /api/v1/orgs/{org_id}."
    />
  );
}
