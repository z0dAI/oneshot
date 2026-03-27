"use client"

import { useEffect, useState } from "react"
import Nav from "@/components/Nav"
import { api, type Profile } from "@/lib/api"

export default function DashboardPage() {
  const [profile, setProfile] = useState<Profile | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .getMe()
      .then((p) => {
        setProfile(p)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-gray-500">Loading...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-red-600">{error}</p>
      </div>
    )
  }

  if (profile && profile.status !== "active") {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4">
        <div className="text-5xl">&#9203;</div>
        <h1 className="text-xl font-semibold text-gray-900">
          {profile.status === "pending"
            ? "Account Pending Approval"
            : "Account Deactivated"}
        </h1>
        <p className="max-w-sm text-center text-gray-600">
          {profile.status === "pending"
            ? "Your organization hasn't been approved yet. An administrator will review your request."
            : "Your account has been deactivated. Contact an administrator for assistance."}
        </p>
        <div className="rounded bg-gray-100 px-4 py-2 text-sm text-gray-500">
          Signed in as {profile.email}
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Nav profile={profile} />
      <main className="mx-auto max-w-4xl px-6 py-10">
        <h1 className="text-2xl font-semibold text-gray-900">
          Welcome back, {profile?.full_name || "there"}
        </h1>
        <p className="mt-1 text-gray-500">
          Role: {profile?.role}
        </p>

        <div className="mt-8 rounded-lg border-2 border-dashed border-gray-300 p-10 text-center text-gray-400">
          Future feature content will go here based on role
        </div>
      </main>
    </div>
  )
}
