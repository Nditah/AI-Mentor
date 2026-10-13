import { SignIn } from "@clerk/nextjs";
import { notFound } from "next/navigation";
import { clerkEnabled } from "@/lib/csp";

export default function SignInPage() {
  if (!clerkEnabled) notFound();
  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <SignIn />
    </div>
  );
}
