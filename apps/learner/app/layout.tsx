import { ClerkProvider } from "@clerk/nextjs";
import type { Metadata } from "next";
import { Fraunces, Source_Sans_3 } from "next/font/google";
import { headers } from "next/headers";
import { AuthBridge } from "@/components/auth-bridge";
import { Providers } from "@/components/providers";
import { clerkEnabled } from "@/lib/csp";
import "./globals.css";
import "katex/dist/katex.min.css";

const sans = Source_Sans_3({ subsets: ["latin"], variable: "--font-sans" });
const display = Fraunces({ subsets: ["latin"], variable: "--font-display" });

export const metadata: Metadata = {
  title: { default: "AI Mentor", template: "%s · AI Mentor" },
  description: "A socratic tutor for AI, machine learning, reinforcement learning, robotics, and research.",
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const nonce = (await headers()).get("x-nonce") ?? undefined;
  const app = <Providers nonce={nonce}>{children}</Providers>;
  return (
    <html lang="en" suppressHydrationWarning className={`${sans.variable} ${display.variable}`}>
      <body className="min-h-screen font-sans antialiased">
        <a className="skip-link" href="#main">
          Skip to content
        </a>
        {clerkEnabled ? (
          <ClerkProvider nonce={nonce}>
            <AuthBridge>{app}</AuthBridge>
          </ClerkProvider>
        ) : (
          app
        )}
      </body>
    </html>
  );
}
