"use client";

import Link from "next/link";
import { Logo } from "@/components/ui/logo";
import { siteConfig } from "@/config/site";
import { useObjectives } from "./store";

export function TopBar() {
  const all = useObjectives();
  const active = all?.filter((o) => !o.archived).length;

  return (
    <header className="topbar">
      <Link
        className="topbar-cell topbar-logo"
        href="/objectives"
        aria-label={`${siteConfig.name} home`}
      >
        <Logo />
      </Link>
      <span className="topbar-cell topbar-tab">{siteConfig.name}</span>
      {/* Empty until the store loads, so the server and first client render match */}
      <span className="topbar-cell topbar-count" role="status">
        {active === undefined ? "" : `${active} active`}
      </span>
      <span className="topbar-cell topbar-status mono">Google Calendar · Preview</span>
    </header>
  );
}
