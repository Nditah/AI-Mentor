"use client";

import { QueuePage } from "@/components/queue-page";

export default function Page() {
  return (
    <QueuePage
      title="Content"
      description="Licensed catalogue and the organisation workspace in Content Studio."
      empty="Open Content Studio to work in an organisation workspace. Instructors consume published releases; they do not own the master repository."
    />
  );
}
