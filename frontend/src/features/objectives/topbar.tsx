"use client";

import Link from "next/link";
import { useState } from "react";
import { Logo } from "@/components/ui/logo";
import { siteConfig } from "@/config/site";
import { googleStartUrl } from "@/features/auth/api";
import { useSession } from "@/features/auth/session";
import { useCalendarStatus } from "@/features/calendar/api";
import { useObjectives } from "./store";

export function TopBar() {
  const all = useObjectives();
  const { user, signOut } = useSession();
  const calendar = useCalendarStatus(user !== null);
  const [failed, setFailed] = useState(false);
  const active = all?.filter((o) => !o.archived).length;

  async function onSignOut() {
    setFailed(false);
    try {
      await signOut();
    } catch {
      setFailed(true);
    }
  }

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
      <div className="topbar-actions">
        {calendar &&
          (calendar.connected ? (
            <span className="topbar-cell topbar-status mono" title={calendar.email ?? undefined}>
              Google Calendar · Connected
            </span>
          ) : (
            <a className="topbar-cell topbar-status topbar-link mono" href={googleStartUrl()}>
              Connect Google Calendar
            </a>
          ))}
        {user && (
          <button type="button" className="topbar-cell topbar-link topbar-out" onClick={onSignOut}>
            {failed ? "Retry Log Out" : "Log Out"}
          </button>
        )}
      </div>
    </header>
  );
}
