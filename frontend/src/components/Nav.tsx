"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { APP_NAME } from "@/lib/config";
import type { Profile } from "@/lib/api";

export function Nav({ profile }: { profile: Profile }) {
  const supabase = createClient();
  const router = useRouter();

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    router.push("/");
  };

  return (
    <nav className="bg-white border-b border-gray-200 px-4 py-3">
      <div className="max-w-6xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link href="/dashboard" className="font-bold text-lg text-gray-900">
            {APP_NAME}
          </Link>
          {profile.role === "admin" && (
            <Link
              href="/admin"
              className="text-sm text-gray-600 hover:text-gray-900"
            >
              Admin Panel
            </Link>
          )}
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-600">
            {profile.full_name || profile.email}
          </span>
          <button
            onClick={handleSignOut}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            Sign out
          </button>
        </div>
      </div>
    </nav>
  );
}
