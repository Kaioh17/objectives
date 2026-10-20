import Image from "next/image";
import Link from "next/link";
import type { ReactNode } from "react";
import banner from "@/assets/banner.jpg";
import { SiteFooter } from "@/components/ui/site-footer";
import { SiteHeader } from "@/components/ui/site-header";
import { siteConfig } from "@/config/site";

export default function MarketingLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <SiteHeader>
        <Link className="topbar-cell topbar-link" href={`${siteConfig.appUrl}/login`}>
          Log In
        </Link>
        <Link className="topbar-cell topbar-link topbar-cta" href={`${siteConfig.appUrl}/signup`}>
          Get Started
        </Link>
      </SiteHeader>
      <Image className="banner" src={banner} alt="" priority sizes="100vw" />
      <main id="main" tabIndex={-1} className="shell">
        {children}
      </main>
      <SiteFooter />
    </>
  );
}
