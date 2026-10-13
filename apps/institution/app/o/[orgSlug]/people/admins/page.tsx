"use client";

import { QueuePage } from "@/components/queue-page";

export default function Page() {
  return (
    <QueuePage
      title="Organisation admins"
      description="Role assignments at organisation scope."
      empty="You are using the v1 instructor/admin rank until scoped RBAC ships. Platform admins still live in the Admin App."
    />
  );
}
