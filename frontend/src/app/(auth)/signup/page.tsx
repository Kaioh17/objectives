import type { Metadata } from "next";
import { AuthForm } from "@/features/auth/auth-form";

export const metadata: Metadata = {
  title: "Create Account",
  description: "Create an account to set objectives and schedule them on your calendar.",
};

export default function SignupPage() {
  return <AuthForm mode="signup" />;
}
