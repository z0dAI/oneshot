"use client";

import { useEffect } from "react";
import { createClient } from "@/lib/supabase/client";

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: Record<string, unknown>) => void;
          prompt: () => void;
        };
      };
    };
  }
}

export function GoogleOneTap() {
  const supabase = createClient();

  useEffect(() => {
    const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
    if (!clientId) return;

    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    document.head.appendChild(script);

    script.onload = () => {
      window.google?.accounts.id.initialize({
        client_id: clientId,
        callback: async (response: { credential: string }) => {
          const { error } = await supabase.auth.signInWithIdToken({
            provider: "google",
            token: response.credential,
          });
          if (!error) {
            window.location.href = "/dashboard";
          }
        },
        auto_select: true,
      });
      window.google?.accounts.id.prompt();
    };

    return () => {
      script.remove();
    };
  }, [supabase]);

  return null;
}
