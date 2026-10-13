import { redirect } from "next/navigation";
import { clerkEnabled } from "@/lib/csp";

const www = process.env.NEXT_PUBLIC_WWW_URL || "http://localhost:3005";

export default async function HomePage() {
  if (clerkEnabled) {
    const { auth } = await import("@clerk/nextjs/server");
    const session = await auth();
    if (session.userId) {
      redirect("/dashboard");
    }
  }
  redirect(www);
}
