"use client";

import { QueuePage } from "@/components/queue-page";

export default function Page() {
  return (
    <QueuePage
      title="People"
      description="Memberships in this organisation."
      empty="No members yet. Invite instructors and learners, or import a roster."
    />
  );
}
