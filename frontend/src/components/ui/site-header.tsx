import Link from "next/link";
import type { ReactNode } from "react";
import { siteConfig } from "@/config/site";
import { Logo } from "./logo";

// Public-page top bar: logo | name ........ optional actions
export function SiteHeader({ children }: { children?: ReactNode }) {
  return (
    <header className="topbar">
      <Link
        className="topbar-cell topbar-logo"
        href={siteConfig.siteUrl}
        aria-label={`${siteConfig.name} home`}
      >
        <Logo />
      </Link>
      <span className="topbar-cell topbar-tab">{siteConfig.name}</span>
      {children && <nav className="topbar-actions">{children}</nav>}
    </header>
  );
}
