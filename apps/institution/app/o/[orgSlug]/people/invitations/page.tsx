"use client";

import { QueuePage } from "@/components/queue-page";

export default function Page() {
  return (
    <QueuePage
      title="Invitations"
      description="Open invites to this organisation."
      empty="No invitations pending."
    />
  );
}
