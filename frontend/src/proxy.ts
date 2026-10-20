import { NextResponse, type NextRequest } from "next/server";
import { siteConfig } from "@/config/site";

const APP_PATHS = ["/login", "/signup", "/objectives"];
const appHost = new URL(siteConfig.appUrl).host;
const siteHost = new URL(siteConfig.siteUrl).host;

// Landing page lives on the site origin; everything else lives on the app origin.
// Any host other than the app host is treated as the site host. One shared host (dev) needs no split.
export function proxy(request: NextRequest) {
  if (appHost === siteHost) return NextResponse.next();
  const { pathname, search } = request.nextUrl;
  const onApp = request.headers.get("host") === appHost;

  if (onApp && pathname === "/") {
    return NextResponse.redirect(new URL("/objectives", siteConfig.appUrl));
  }
  if (!onApp && APP_PATHS.some((p) => pathname === p || pathname.startsWith(`${p}/`))) {
    return NextResponse.redirect(new URL(pathname + search, siteConfig.appUrl));
  }
  return NextResponse.next();
}

export const config = { matcher: ["/((?!_next/|api/|.*\\..*).*)"] };
