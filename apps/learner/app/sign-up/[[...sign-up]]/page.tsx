import { SignUp } from "@clerk/nextjs";
import { notFound } from "next/navigation";
import { clerkEnabled } from "@/lib/csp";

export default function SignUpPage() {
  if (!clerkEnabled) notFound();
  return (
    <main id="main" className="flex min-h-screen items-center justify-center px-5 py-10">
      <SignUp />
    </main>
  );
}
