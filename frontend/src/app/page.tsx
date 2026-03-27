"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Script from "next/script"
import { createClient } from "@/lib/supabase/client"
import { APP_NAME } from "@/lib/config"

async function generateNonce(): Promise<[string, string]> {
  const randomValues = crypto.getRandomValues(new Uint8Array(32))
  const nonce = Array.from(randomValues, (byte) => byte.toString(36)).join("")
  const encoder = new TextEncoder()
  const encodedNonce = encoder.encode(nonce)
  const hashBuffer = await crypto.subtle.digest("SHA-256", encodedNonce)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  const hashedNonce = hashArray.map((b) => b.toString(16).padStart(2, "0")).join("")
  return [nonce, hashedNonce]
}

export default function LoginPage() {
  const router = useRouter()
  const supabase = createClient()
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    supabase.auth.getUser().then(({ data: { user } }) => {
      if (user) {
        router.replace("/dashboard")
      } else {
        setLoading(false)
      }
    })
  }, [router, supabase])

  async function initializeGoogleOneTap() {
    const [nonce, hashedNonce] = await generateNonce()

    google.accounts.id.initialize({
      client_id: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID!,
      callback: async (response: GoogleCredentialResponse) => {
        const { error } = await supabase.auth.signInWithIdToken({
          provider: "google",
          token: response.credential,
          nonce,
        })
        if (error) {
          setError("Sign-in failed. Please try again.")
        } else {
          router.push("/dashboard")
        }
      },
      nonce: hashedNonce,
      use_fedcm_for_prompt: true,
      auto_select: true,
    })

    google.accounts.id.prompt()

    const buttonEl = document.getElementById("google-signin-button")
    if (buttonEl) {
      google.accounts.id.renderButton(buttonEl, {
        theme: "outline",
        size: "large",
        text: "signin_with",
        width: 300,
      })
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-gray-500">Loading...</p>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-8 bg-gray-50">
      <Script
        src="https://accounts.google.com/gsi/client"
        onReady={() => { void initializeGoogleOneTap() }}
      />

      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900">{APP_NAME}</h1>
        <p className="mt-2 text-gray-600">Sign in to continue</p>
      </div>

      <div id="google-signin-button" />

      {error && (
        <p className="text-sm text-red-600">{error}</p>
      )}
    </div>
  )
}
