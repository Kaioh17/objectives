import Image from "next/image";
import type { ReactNode } from "react";
import banner from "@/assets/banner.jpg";
import { SiteFooter } from "@/components/ui/site-footer";
import { TopBar } from "@/features/objectives/topbar";

export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <TopBar />
      <Image className="banner" src={banner} alt="" priority sizes="100vw" />
      <main id="main" tabIndex={-1} className="shell">
        {children}
      </main>
      <SiteFooter dock />
    </>
  );
}
