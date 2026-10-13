import type { Metadata } from "next";
import { AuthPanel } from "@/components/auth-panel";
import { AuthReset } from "@/components/auth-reset";

export const metadata: Metadata = {
  title: "Sign in | AI Mentor",
  description: "Sign in to the AI Mentor Learner App. Staff roles are granted separately.",
  robots: { index: false, follow: false },
};

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ reset?: string }>;
}) {
  if ((await searchParams).reset === "1") return <AuthReset />;
  return <AuthPanel mode="login" />;
}
