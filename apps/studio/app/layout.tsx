import { ClerkProvider } from "@clerk/nextjs";
import type { Metadata } from "next";
import { Source_Sans_3 } from "next/font/google";
import { headers } from "next/headers";
import { AuthBridge } from "@/components/auth-bridge";
import { Providers } from "@/components/providers";
import { Shell } from "@/components/shell";
import { clerkEnabled } from "@/lib/csp";
import "./globals.css";

const sans = Source_Sans_3({ subsets: ["latin"], variable: "--font-sans" });

export const metadata: Metadata = {
  title: { default: "Admin", template: "%s · AI Mentor Admin" },
  description: "Curate the knowledge library, review drafts, and manage the studio.",
  robots: { index: false, follow: false },
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const nonce = (await headers()).get("x-nonce") ?? undefined;
  const app = (
    <Providers>
      <Shell>{children}</Shell>
    </Providers>
  );
  return (
    <html lang="en" className={sans.variable}>
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
