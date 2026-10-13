"use client";

import { AuthChrome } from "@/components/auth-chrome";
import { Footer } from "@/components/footer";
import { Header } from "@/components/header";
import { StickyCta } from "@/components/sticky-cta";
import { isAuthPath } from "@/lib/urls";
import { usePathname } from "next/navigation";

export function Chrome({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() || "/";
  if (isAuthPath(pathname)) {
    return <AuthChrome>{children}</AuthChrome>;
  }
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main id="main" className="flex-1">
        {children}
      </main>
      <StickyCta />
      <Footer />
    </div>
  );
}
