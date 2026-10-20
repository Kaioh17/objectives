import Image from "next/image";
import type { ReactNode } from "react";
import banner from "@/assets/banner.jpg";
import { SiteFooter } from "@/components/ui/site-footer";
import { Greeting } from "@/features/auth/greeting";
import { SessionGate, SessionProvider } from "@/features/auth/session";
import { TopBar } from "@/features/objectives/topbar";

export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <SessionProvider>
      <TopBar />
      <div className="banner-wrap">
        <Image className="banner" src={banner} alt="" priority sizes="100vw" />
        <Greeting />
      </div>
      <main id="main" tabIndex={-1} className="shell">
        <SessionGate>{children}</SessionGate>
      </main>
      <SiteFooter dock />
    </SessionProvider>
  );
}
