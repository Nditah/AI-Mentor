"use client";

import { QueuePage } from "@/components/queue-page";

export default function Page() {
  return (
    <QueuePage
      title="New cohort"
      description="Lead instructors create a cohort, pin a release, and invite staff."
      empty="Cohort creation will call POST /api/v1/orgs/{org_id}/cohorts when tenancy lands. Until then this form is not submitted."
    />
  );
}
