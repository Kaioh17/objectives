import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

// Liveness probe for load balancers and container orchestrators
export function GET() {
  return NextResponse.json({ message: "ok" });
}
