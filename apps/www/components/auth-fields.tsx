"use client";

import { Button } from "@/components/ui/button";
import { loginUrl, registerUrl } from "@/lib/urls";

export const inputClass =
  "mt-1 w-full rounded-2xl border border-slate-300 bg-white px-3 py-2.5 text-base dark:border-slate-600 dark:bg-slate-950";

export type AuthMode = "login" | "register";

export function Field({
  label,
  htmlFor,
  children,
}: {
  label: string;
  htmlFor: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block font-semibold" htmlFor={htmlFor}>
      {label}
      {children}
    </label>
  );
}

export function AuthFields({
  mode,
  error,
  pending,
  extra,
}: {
  mode: AuthMode;
  error: string;
  pending: boolean;
  extra?: React.ReactNode;
}) {
  const register = mode === "register";
  return (
    <>
      {register ? (
        <Field label="Name" htmlFor="name">
          <input id="name" name="name" autoComplete="name" maxLength={120} className={inputClass} />
        </Field>
      ) : null}
      <Field label="Email" htmlFor="email">
        <input
          id="email"
          name="email"
          type="email"
          required
          autoComplete="email"
          maxLength={320}
          className={inputClass}
        />
      </Field>
      <Field label="Password" htmlFor="password">
        <input
          id="password"
          name="password"
          type="password"
          required
          minLength={register ? 8 : undefined}
          autoComplete={register ? "new-password" : "current-password"}
          className={inputClass}
        />
      </Field>
      {register ? (
        <>
          <Field label="Confirm password" htmlFor="confirm">
            <input
              id="confirm"
              name="confirm"
              type="password"
              required
              minLength={8}
              autoComplete="new-password"
              className={inputClass}
            />
          </Field>
          <label className="flex items-start gap-3 text-sm font-medium">
            <input id="age" name="age" type="checkbox" value="yes" className="mt-1 h-5 w-5" />
            <span>I am 16 or over</span>
          </label>
          <label className="flex items-start gap-3 text-sm font-medium">
            <input id="terms" name="terms" type="checkbox" value="yes" className="mt-1 h-5 w-5" />
            <span>
              I agree to the{" "}
              <a className="text-[#1d4ed8] underline" href="/legal/terms">
                terms
              </a>{" "}
              and{" "}
              <a className="text-[#1d4ed8] underline" href="/legal/privacy">
                privacy policy
              </a>
            </span>
          </label>
        </>
      ) : (
        <p className="text-sm">
          <a className="font-semibold text-[#1d4ed8]" href="/login?reset=1">
            Forgot password
          </a>
        </p>
      )}
      {error ? <p className="text-sm text-red-700 dark:text-red-300">{error}</p> : null}
      <Button type="submit" className="w-full" disabled={pending}>
        {pending ? "Continuing" : register ? "Create account" : "Sign in"}
      </Button>
      {extra}
      <p className="text-center text-sm text-slate-600 dark:text-slate-400">
        {register ? (
          <>
            Already have an account?{" "}
            <a className="font-semibold text-[#1d4ed8]" href={loginUrl}>
              Sign in
            </a>
          </>
        ) : (
          <>
            New here?{" "}
            <a className="font-semibold text-[#1d4ed8]" href={registerUrl}>
              Create an account
            </a>
          </>
        )}
      </p>
    </>
  );
}

export function GoogleButton({ onClick, disabled }: { onClick: () => void; disabled: boolean }) {
  return (
    <Button type="button" variant="quiet" className="w-full" disabled={disabled} onClick={onClick}>
      Continue with Google
    </Button>
  );
}

export function clerkMessage(caught: unknown): string {
  if (typeof caught === "object" && caught && "errors" in caught) {
    const errors = (caught as { errors?: { longMessage?: string; message?: string }[] }).errors;
    const first = errors?.[0];
    if (first?.longMessage) return first.longMessage;
    if (first?.message) return first.message;
  }
  if (caught instanceof Error && caught.message) return caught.message;
  return "That did not work. Check the fields and try again.";
}
