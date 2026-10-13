"use client";

import { QueuePage } from "@/components/queue-page";

export default function Page() {
  return (
    <QueuePage
      title="Licences"
      description="Seats this organisation has bought."
      empty="No licences on file. Billing is Stripe Checkout on the Learner App until organisation invoices ship."
    />
  );
}
