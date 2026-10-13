"use client";

import { useState, type FormEvent } from "react";
import { AuthFields, type AuthMode } from "@/components/auth-fields";
import { clerkEnabled, devAuth } from "@/lib/clerk";
import { dashboardUrl } from "@/lib/urls";
import { ClerkAuthForm } from "@/components/clerk-auth-form";

export function AuthForm({ mode }: { mode: AuthMode }) {
  if (clerkEnabled) return <ClerkAuthForm mode={mode} />;
  return <LocalAuthForm mode={mode} />;
}

function LocalAuthForm({ mode }: { mode: AuthMode }) {
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const register = mode === "register";

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const data = new FormData(event.currentTarget);
    const email = String(data.get("email") || "").trim();
    const password = String(data.get("password") || "");
    if (!email || !password) {
      setError("Enter your email and password.");
      return;
    }
    if (register) {
      const confirm = String(data.get("confirm") || "");
      if (password.length < 8) {
        setError("Use at least 8 characters for the password.");
        return;
      }
      if (password !== confirm) {
        setError("The passwords do not match.");
        return;
      }
      if (data.get("age") !== "yes") {
        setError("You must be 16 or over to create an account.");
        return;
      }
      if (data.get("terms") !== "yes") {
        setError("Agree to the terms and privacy policy to continue.");
        return;
      }
    }
    if (!devAuth) {
      setError("Sign-in is not configured yet. Set Clerk keys, or enable local DEV_AUTH.");
      return;
    }
    setPending(true);
    window.location.assign(dashboardUrl);
  }

  return (
    <form
      className="space-y-4 rounded-3xl border border-slate-200 bg-white p-6 shadow-card dark:border-slate-700 dark:bg-slate-900"
      onSubmit={onSubmit}
    >
      <AuthFields mode={mode} error={error} pending={pending} />
      {devAuth ? (
        <p className="text-sm text-slate-600 dark:text-slate-400">
          Local development continues in the Learner App with the demo session switcher. Production sign-in uses
          Clerk.
        </p>
      ) : null}
    </form>
  );
}

export type { AuthMode };
