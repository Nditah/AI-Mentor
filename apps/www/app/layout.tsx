import type { Metadata } from "next";
import { Fraunces, Source_Sans_3 } from "next/font/google";
import { headers } from "next/headers";
import { Chrome } from "@/components/chrome";
import { Providers } from "@/components/providers";
import { wwwUrl } from "@/lib/urls";
import "./globals.css";

const sans = Source_Sans_3({ subsets: ["latin"], variable: "--font-sans" });
const display = Fraunces({ subsets: ["latin"], variable: "--font-display" });

export const metadata: Metadata = {
  metadataBase: new URL(wwwUrl),
  title: { default: "AI Mentor — a tutor that asks before it explains", template: "%s" },
  description:
    "Learn AI, machine learning, reinforcement learning, and robotics with a Socratic tutor, a restricted coding lab, and a governed knowledge catalog.",
  openGraph: {
    type: "website",
    siteName: "AI Mentor",
    locale: "en",
  },
  alternates: {
    languages: { en: "/", "x-default": "/" },
  },
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const nonce = (await headers()).get("x-nonce") ?? undefined;
  const jsonLd = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "Organization",
        name: "AI Mentor",
        url: wwwUrl,
        description: "A Socratic tutor, governed curriculum, restricted lab, and research desk for AI.",
      },
      {
        "@type": "WebSite",
        name: "AI Mentor",
        url: wwwUrl,
      },
    ],
  };
  return (
    <html lang="en" suppressHydrationWarning className={`${sans.variable} ${display.variable}`}>
      <body className="min-h-screen font-sans antialiased">
        <a className="skip-link" href="#main">
          Skip to content
        </a>
        <script
          nonce={nonce}
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
        <Providers nonce={nonce}>
          <Chrome>{children}</Chrome>
        </Providers>
      </body>
    </html>
  );
}
