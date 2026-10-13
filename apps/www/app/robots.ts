import type { MetadataRoute } from "next";
import { wwwUrl } from "@/lib/urls";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: { userAgent: "*", allow: "/" },
    sitemap: `${wwwUrl}/sitemap.xml`,
  };
}
