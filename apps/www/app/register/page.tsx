import type { Metadata } from "next";
import { AuthPanel } from "@/components/auth-panel";

export const metadata: Metadata = {
  title: "Create an account | AI Mentor",
  description: "Start learning free. You must be 16 or over. After you register you land on the Learner App.",
  robots: { index: false, follow: false },
};

export default function RegisterPage() {
  return <AuthPanel mode="register" />;
}
