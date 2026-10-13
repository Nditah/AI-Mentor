"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export type AppLink = {
  code: string;
  name: string;
  url: string;
  available: boolean;
};

export function AppLauncher({ current }: { current: string }) {
  const apps = useQuery({
    queryKey: ["me-apps"],
    queryFn: () => api<AppLink[]>("/api/v1/me/apps"),
  });
  const items = (apps.data || []).filter((item) => item.available && item.code !== current);
  if (!items.length) return null;
  return (
    <nav aria-label="Applications" className="mt-3 flex flex-col gap-1 text-sm">
      {items.map((item) => (
        <a key={item.code} className="rounded-full px-3 py-1 text-[#1d4ed8] underline" href={item.url}>
          {item.name}
        </a>
      ))}
    </nav>
  );
}
