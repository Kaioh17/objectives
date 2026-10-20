import type { ReactNode } from "react";
import { SiteFooter } from "@/components/ui/site-footer";
import { SiteHeader } from "@/components/ui/site-header";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <SiteHeader />
      <main id="main" tabIndex={-1} className="shell auth-shell">
        {children}
      </main>
      <SiteFooter />
    </>
  );
}
