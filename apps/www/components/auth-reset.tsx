"use client";

import { useSignIn } from "@clerk/nextjs";
import { useState, type FormEvent } from "react";
import { Field, clerkMessage, inputClass } from "@/components/auth-fields";
import { Button } from "@/components/ui/button";
import { clerkEnabled } from "@/lib/clerk";
import { loginUrl } from "@/lib/urls";

export function AuthReset() {
  if (clerkEnabled) return <ClerkReset />;
  return (
    <section className="mx-auto w-full max-w-md px-5 py-16">
      <h1 className="font-display text-4xl tracking-tight">Reset your password</h1>
      <p className="mt-4 text-slate-700 dark:text-slate-300">
        Password reset email is sent when Clerk is configured. Until then, use the Learner App session switcher in
        local development.
      </p>
      <p className="mt-6">
        <a className="font-semibold text-[#1d4ed8]" href={loginUrl}>
          Back to sign in
        </a>
      </p>
    </section>
  );
}

function ClerkReset() {
  const { isLoaded, signIn } = useSignIn();
  const [error, setError] = useState("");
  const [sent, setSent] = useState(false);
  const [pending, setPending] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (!isLoaded || !signIn) return;
    const email = String(new FormData(event.currentTarget).get("email") || "").trim();
    setPending(true);
    try {
      await signIn.create({ strategy: "reset_password_email_code", identifier: email });
      setSent(true);
    } catch (caught) {
      setError(clerkMessage(caught));
    }
    setPending(false);
  }

  return (
    <section className="mx-auto w-full max-w-md px-5 py-16">
      <h1 className="font-display text-4xl tracking-tight">Reset your password</h1>
      {sent ? (
        <p className="mt-4 text-slate-700 dark:text-slate-300">
          If that email has an account, a reset code is on its way. Then sign in with the new password.
        </p>
      ) : (
        <form className="mt-6 space-y-4" onSubmit={onSubmit}>
          <Field label="Email" htmlFor="email">
            <input id="email" name="email" type="email" required autoComplete="email" className={inputClass} />
          </Field>
          {error ? <p className="text-sm text-red-700 dark:text-red-300">{error}</p> : null}
          <Button type="submit" className="w-full" disabled={pending}>
            {pending ? "Sending" : "Send reset email"}
          </Button>
        </form>
      )}
      <p className="mt-6">
        <a className="font-semibold text-[#1d4ed8]" href={loginUrl}>
          Back to sign in
        </a>
      </p>
    </section>
  );
}
