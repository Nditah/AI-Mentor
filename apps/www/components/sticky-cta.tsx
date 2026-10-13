"use client";

import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { pages } from "@/lib/pages";
import { ctas } from "@/lib/urls";

export function StickyCta() {
  const pathname = usePathname() || "/";
  const spec = pages[pathname.replace(/^\//, "")];
  if (!spec || pathname.startsWith("/demo") || pathname.startsWith("/company/contact")) return null;
  const cta = ctas[spec.cta];
  return (
    <div className="sticky bottom-0 z-30 border-t border-slate-200 bg-[var(--paper)] p-3 lg:hidden dark:border-slate-800">
      <Button href={cta.href} className="w-full">
        {cta.label}
      </Button>
    </div>
  );
}
