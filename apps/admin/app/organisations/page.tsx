"use client";

import { QueuePage } from "@/components/queue-page";

export default function OrganisationsPage() {
  return (
    <QueuePage
      title="Organisations"
      description="Every tenant on the platform. Membership, licences, and SSO status will list here."
      empty="Tenancy is not in the v1 schema yet. Demo organisation slug is demo. Create tenants after the organisations table lands."
    />
  );
}
