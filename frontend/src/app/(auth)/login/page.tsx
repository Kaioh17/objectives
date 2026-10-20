import type { Metadata } from "next";
import { AuthForm } from "@/features/auth/auth-form";

export const metadata: Metadata = {
  title: "Log In",
  description: "Log in to see your daily, weekly and monthly objectives.",
};

export default function LoginPage() {
  return <AuthForm mode="login" />;
}
