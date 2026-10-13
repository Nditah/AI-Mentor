"use client";

import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { submitLead, type LeadPayload } from "@/lib/api";

type Variant = "instructor" | "enterprise" | "contact";

const kinds: Record<Variant, LeadPayload["kind"][]> = {
  instructor: ["instructor"],
  enterprise: ["enterprise"],
  contact: ["sales", "support", "partnership", "enterprise", "content"],
};

export function DemoForm({ variant }: { variant: Variant }) {
  const [status, setStatus] = useState<"idle" | "sending" | "ok" | "error">("idle");
  const [message, setMessage] = useState("");
  const [kind, setKind] = useState<LeadPayload["kind"]>(kinds[variant][0]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const seats = Number(data.get("seats") || data.get("cohort_size") || "");
    const payload: LeadPayload = {
      kind,
      name: String(data.get("name") || ""),
      email: String(data.get("email") || ""),
      organisation: String(data.get("organisation") || "") || undefined,
      role: String(data.get("role") || "") || undefined,
      country: String(data.get("country") || "") || undefined,
      start_month: String(data.get("start_month") || "") || undefined,
      message: String(data.get("message") || ""),
      website: String(data.get("website") || ""),
    };
    if (Number.isFinite(seats) && seats >= 1) {
      if (variant === "instructor") payload.cohort_size = seats;
      else payload.seats = seats;
    }
    const lms = String(data.get("lms") || "");
    if (lms === "canvas" || lms === "moodle" || lms === "other" || lms === "none") payload.lms = lms;
    const sso = String(data.get("sso") || "");
    if (sso === "yes") payload.sso = true;
    if (sso === "no") payload.sso = false;
    setStatus("sending");
    const result = await submitLead(payload);
    setStatus(result.ok ? "ok" : "error");
    setMessage(result.message);
    if (result.ok) form.reset();
  }

  if (status === "ok") {
    return (
      <p className="rounded-3xl border border-emerald-200 bg-emerald-50 p-6 text-slate-800 dark:border-emerald-900 dark:bg-emerald-950 dark:text-slate-100">
        {message}
      </p>
    );
  }

  return (
    <form className="space-y-4 rounded-3xl border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900" onSubmit={onSubmit}>
      {variant === "contact" ? (
        <Field label="What do you need?">
          <select
            className={inputClass}
            value={kind}
            onChange={(event) => setKind(event.target.value as LeadPayload["kind"])}
          >
            <option value="sales">Sales</option>
            <option value="support">Support</option>
            <option value="partnership">Partnerships</option>
            <option value="enterprise">Enterprise demo</option>
            <option value="content">Content / CLO</option>
          </select>
        </Field>
      ) : null}
      <Field label="Name" htmlFor="name">
        <input id="name" name="name" required maxLength={120} className={inputClass} autoComplete="name" />
      </Field>
      <Field label="Work email" htmlFor="email">
        <input id="email" name="email" type="email" required maxLength={320} className={inputClass} autoComplete="email" />
      </Field>
      <Field label="Organisation" htmlFor="organisation">
        <input id="organisation" name="organisation" maxLength={200} className={inputClass} autoComplete="organization" />
      </Field>
      {variant === "instructor" ? (
        <>
          <Field label="Role" htmlFor="role">
            <input id="role" name="role" maxLength={80} className={inputClass} />
          </Field>
          <Field label="Cohort size" htmlFor="cohort_size">
            <input id="cohort_size" name="cohort_size" type="number" min={1} className={inputClass} />
          </Field>
          <Field label="Start month" htmlFor="start_month">
            <input id="start_month" name="start_month" maxLength={20} className={inputClass} placeholder="2026-03" />
          </Field>
        </>
      ) : null}
      {variant === "enterprise" || kind === "enterprise" ? (
        <>
          <Field label="Country" htmlFor="country">
            <input id="country" name="country" maxLength={80} className={inputClass} />
          </Field>
          <Field label="Approximate seats" htmlFor="seats">
            <input id="seats" name="seats" type="number" min={1} className={inputClass} />
          </Field>
          <Field label="SSO required?" htmlFor="sso">
            <select id="sso" name="sso" className={inputClass} defaultValue="">
              <option value="">Not sure</option>
              <option value="yes">Yes</option>
              <option value="no">No</option>
            </select>
          </Field>
          <Field label="LMS" htmlFor="lms">
            <select id="lms" name="lms" className={inputClass} defaultValue="none">
              <option value="none">None</option>
              <option value="canvas">Canvas</option>
              <option value="moodle">Moodle</option>
              <option value="other">Other</option>
            </select>
          </Field>
        </>
      ) : null}
      <Field label="Message" htmlFor="message">
        <textarea id="message" name="message" rows={4} maxLength={4000} className={inputClass} />
      </Field>
      <div className="hidden" aria-hidden="true">
        <label htmlFor="website">Website</label>
        <input id="website" name="website" tabIndex={-1} autoComplete="off" />
      </div>
      {status === "error" ? <p className="text-sm text-red-700 dark:text-red-300">{message}</p> : null}
      <p className="text-sm text-slate-600 dark:text-slate-400">
        Submitting does not create an account or grant an app role.
      </p>
      <Button type="submit" disabled={status === "sending"}>
        {status === "sending" ? "Sending" : "Submit"}
      </Button>
    </form>
  );
}

const inputClass =
  "mt-1 w-full rounded-2xl border border-slate-300 bg-white px-3 py-2 text-base dark:border-slate-600 dark:bg-slate-950";

function Field({
  label,
  htmlFor,
  children,
}: {
  label: string;
  htmlFor?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block font-semibold" htmlFor={htmlFor}>
      {label}
      {children}
    </label>
  );
}
