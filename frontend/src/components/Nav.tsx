"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { createClient } from "@/lib/supabase/client"
import { APP_NAME } from "@/lib/config"
import type { Profile } from "@/lib/api"

export default function Nav({ profile }: { profile: Profile | null }) {
  const router = useRouter()
  const supabase = createClient()

  async function handleSignOut() {
    await supabase.auth.signOut()
    router.push("/")
  }

  const initials = profile?.full_name
    ? profile.full_name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "?"

  return (
    <nav className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-3">
      <Link href="/dashboard" className="text-lg font-bold text-gray-900">
        {APP_NAME}
      </Link>

      <div className="flex items-center gap-4">
        {profile?.role === "admin" && (
          <Link
            href="/admin"
            className="rounded border border-indigo-500 px-3 py-1 text-sm font-medium text-indigo-600 hover:bg-indigo-50"
          >
            Admin Panel
          </Link>
        )}

        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-600 text-sm font-semibold text-white">
            {initials}
          </div>
          <button
            onClick={() => { void handleSignOut() }}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            Sign out
          </button>
        </div>
      </div>
    </nav>
  )
}
