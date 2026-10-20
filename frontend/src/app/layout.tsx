import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono, Newsreader } from "next/font/google";
import type { ReactNode } from "react";
import { siteConfig } from "@/config/site";
import "@/styles/globals.css";

const sans = Geist({ subsets: ["latin"], variable: "--font-sans" });
const serif = Newsreader({ subsets: ["latin"], variable: "--font-serif" });
const mono = Geist_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: { default: siteConfig.name, template: `%s | ${siteConfig.name}` },
  description: siteConfig.description,
};

// Zoom stays enabled (never set maximumScale / userScalable)
export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#fbfbfa" },
    { media: "(prefers-color-scheme: dark)", color: "#191919" },
  ],
};

// Chrome (header, <main>, footer) lives in the route-group layouts: (marketing), (auth), (app)
export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={`${sans.variable} ${serif.variable} ${mono.variable}`}>
      <body>
        <a className="skip-link" href="#main">
          Skip to Main Content
        </a>
        {children}
      </body>
    </html>
  );
}
