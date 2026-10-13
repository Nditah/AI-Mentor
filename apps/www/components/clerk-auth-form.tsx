"use client";

import { useSignIn, useSignUp } from "@clerk/nextjs";
import { useState, type FormEvent } from "react";
import { AuthFields, GoogleButton, clerkMessage, inputClass, Field, type AuthMode } from "@/components/auth-fields";
import { Button } from "@/components/ui/button";
import { dashboardUrl } from "@/lib/urls";

export function ClerkAuthForm({ mode }: { mode: AuthMode }) {
  const register = mode === "register";
  const signInApi = useSignIn();
  const signUpApi = useSignUp();
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const [needsCode, setNeedsCode] = useState(false);

  async function onGoogle() {
    setError("");
    try {
      if (register) {
        if (!signUpApi.signUp) return;
        await signUpApi.signUp.authenticateWithRedirect({
          strategy: "oauth_google",
          redirectUrl: `${window.location.origin}/register`,
          redirectUrlComplete: dashboardUrl,
        });
        return;
      }
      if (!signInApi.signIn) return;
      await signInApi.signIn.authenticateWithRedirect({
        strategy: "oauth_google",
        redirectUrl: `${window.location.origin}/login`,
        redirectUrlComplete: dashboardUrl,
      });
    } catch (caught) {
      setError(clerkMessage(caught));
    }
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const data = new FormData(event.currentTarget);
    const email = String(data.get("email") || "").trim();
    const password = String(data.get("password") || "");
    const code = String(data.get("code") || "").trim();
    setPending(true);
    try {
      if (register) {
        if (!signUpApi.isLoaded || !signUpApi.signUp) {
          setError("Sign-up is still loading. Try again in a moment.");
          setPending(false);
          return;
        }
        if (needsCode) {
          const attempt = await signUpApi.signUp.attemptEmailAddressVerification({ code });
          if (attempt.status === "complete") {
            await signUpApi.setActive({ session: attempt.createdSessionId });
            window.location.assign(dashboardUrl);
            return;
          }
          setError("Enter the code from your email.");
        } else {
          const confirm = String(data.get("confirm") || "");
          if (password !== confirm) {
            setError("The passwords do not match.");
            setPending(false);
            return;
          }
          if (data.get("age") !== "yes") {
            setError("You must be 16 or over to create an account.");
            setPending(false);
            return;
          }
          if (data.get("terms") !== "yes") {
            setError("Agree to the terms and privacy policy to continue.");
            setPending(false);
            return;
          }
          const name = String(data.get("name") || "").trim();
          const [firstName, ...rest] = name.split(/\s+/);
          await signUpApi.signUp.create({
            emailAddress: email,
            password,
            firstName: firstName || undefined,
            lastName: rest.join(" ") || undefined,
          });
          await signUpApi.signUp.prepareEmailAddressVerification({ strategy: "email_code" });
          setNeedsCode(true);
        }
      } else {
        if (!signInApi.isLoaded || !signInApi.signIn) {
          setError("Sign-in is still loading. Try again in a moment.");
          setPending(false);
          return;
        }
        const result = await signInApi.signIn.create({ identifier: email, password });
        if (result.status === "complete") {
          await signInApi.setActive({ session: result.createdSessionId });
          window.location.assign(dashboardUrl);
          return;
        }
        setError("Additional verification is required. Try Google, or finish sign-in in the Learner App.");
      }
    } catch (caught) {
      setError(clerkMessage(caught));
    }
    setPending(false);
  }

  if (needsCode) {
    return (
      <form className="space-y-4 rounded-3xl border border-slate-200 bg-white p-6 shadow-card dark:border-slate-700 dark:bg-slate-900" onSubmit={onSubmit}>
        <p className="text-sm text-slate-700 dark:text-slate-300">We sent a short code to your email.</p>
        <Field label="Email code" htmlFor="code">
          <input
            id="code"
            name="code"
            inputMode="numeric"
            autoComplete="one-time-code"
            required
            className={inputClass}
          />
        </Field>
        {error ? <p className="text-sm text-red-700 dark:text-red-300">{error}</p> : null}
        <Button type="submit" className="w-full" disabled={pending}>
          {pending ? "Checking" : "Verify email"}
        </Button>
      </form>
    );
  }

  return (
    <form className="space-y-4 rounded-3xl border border-slate-200 bg-white p-6 shadow-card dark:border-slate-700 dark:bg-slate-900" onSubmit={onSubmit}>
      <AuthFields mode={mode} error={error} pending={pending} extra={<GoogleButton disabled={pending} onClick={onGoogle} />} />
    </form>
  );
}
