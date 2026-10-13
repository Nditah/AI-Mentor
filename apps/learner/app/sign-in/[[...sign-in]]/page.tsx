import { SignIn } from "@clerk/nextjs";
import { notFound } from "next/navigation";
import { clerkEnabled } from "@/lib/csp";

export default function SignInPage() {
  if (!clerkEnabled) notFound();
  return (
    <main id="main" className="flex min-h-screen items-center justify-center px-5 py-10">
      <SignIn />
    </main>
  );
}
