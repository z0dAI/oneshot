"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, APIError } from "@/lib/api";
import { Nav } from "@/components/Nav";
import { APP_NAME } from "@/lib/config";
import type { Profile } from "@/lib/api";

export default function DashboardPageClient() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    api
      .getMe()
      .then(setProfile)
      .catch((err: unknown) => {
        if (err instanceof APIError && err.status === 401) {
          router.push("/");
        }
      })
      .finally(() => setLoading(false));
  }, [router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-500">
        Loading...
      </div>
    );
  }

  if (!profile) return null;

  // Pending or archived — show status message instead of dashboard
  if (profile.status === "pending") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md text-center p-8 bg-white rounded-lg shadow">
          <h1 className="text-2xl font-bold text-gray-900">
            Account Pending Approval
          </h1>
          <p className="mt-3 text-gray-600">
            Your account ({profile.email}) is awaiting approval from an
            administrator.
          </p>
          <p className="mt-1 text-sm text-gray-400">
            You&apos;ll get access once your domain is approved or an admin
            activates your account.
          </p>
        </div>
      </div>
    );
  }

  if (profile.status === "archived") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md text-center p-8 bg-white rounded-lg shadow">
          <h1 className="text-2xl font-bold text-gray-900">
            Account Deactivated
          </h1>
          <p className="mt-3 text-gray-600">
            Your account ({profile.email}) has been deactivated. Please contact
            an administrator if you believe this is an error.
          </p>
        </div>
      </div>
    );
  }

  // Active user — show dashboard
  return (
    <div className="min-h-screen bg-gray-50">
      <Nav profile={profile} />
      <main className="max-w-4xl mx-auto py-8 px-4">
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome, {profile.full_name || profile.email}
        </h1>
        <p className="mt-1 text-gray-600 capitalize">Role: {profile.role}</p>
        <div className="mt-8 p-6 bg-white rounded-lg border border-gray-200">
          <p className="text-gray-500">
            {APP_NAME} dashboard. Additional features will appear here based on
            your role.
          </p>
        </div>
      </main>
    </div>
  );
}
