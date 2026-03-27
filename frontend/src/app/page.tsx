"use client";

import dynamic from "next/dynamic";

const LoginPageClient = dynamic(() => import("@/components/LoginPageClient"), {
  ssr: false,
});

export default function LoginPage() {
  return <LoginPageClient />;
}
