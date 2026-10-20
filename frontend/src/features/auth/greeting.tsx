"use client";

import { useSession } from "./session";

export function Greeting() {
  const { user } = useSession();
  if (!user) return null;
  return <p className="banner-greeting">Hello, {user.full_name || user.email.split("@")[0]}</p>;
}
