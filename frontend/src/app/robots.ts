import type { MetadataRoute } from "next";
import { siteConfig } from "@/config/site";

// Prod switch: only production is indexable; dev and staging are hidden from crawlers
export default function robots(): MetadataRoute.Robots {
  return {
    rules: siteConfig.isProduction
      ? { userAgent: "*", allow: "/" }
      : { userAgent: "*", disallow: "/" },
  };
}
