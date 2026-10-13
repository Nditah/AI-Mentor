import type { MetadataRoute } from "next";
import { sitemapPaths } from "@/lib/pages";
import { wwwUrl } from "@/lib/urls";

export default function sitemap(): MetadataRoute.Sitemap {
  return sitemapPaths.map((path) => ({
    url: `${wwwUrl}${path === "/" ? "" : path}`,
    changeFrequency: path === "/" ? "weekly" : "monthly",
    priority: path === "/" ? 1 : 0.7,
  }));
}
