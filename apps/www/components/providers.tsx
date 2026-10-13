"use client";

import { ClerkProvider } from "@clerk/nextjs";
import { ThemeProvider } from "next-themes";
import { clerkEnabled } from "@/lib/clerk";

export function Providers({ children, nonce }: { children: React.ReactNode; nonce?: string }) {
  const theme = (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem nonce={nonce}>
      {children}
    </ThemeProvider>
  );
  if (!clerkEnabled) return theme;
  return (
    <ClerkProvider nonce={nonce} signInUrl="/login" signUpUrl="/register" afterSignOutUrl="/">
      {theme}
    </ClerkProvider>
  );
}
