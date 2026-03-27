import { createClient } from "@/lib/supabase/client"
import { API_URL } from "@/lib/config"

async function getAuthHeaders(): Promise<Record<string, string>> {
  const supabase = createClient()
  const {
    data: { session },
  } = await supabase.auth.getSession()

  if (!session?.access_token) {
    throw new Error("Not authenticated")
  }

  return {
    Authorization: `Bearer ${session.access_token}`,
    "Content-Type": "application/json",
  }
}

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { ...headers, ...options.headers },
  })

  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail || `API error: ${response.status}`)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json()
}

export const api = {
  getMe: () => apiFetch<Profile>("/api/me"),
  updateMe: (data: { full_name?: string; avatar_url?: string }) =>
    apiFetch<Profile>("/api/me", { method: "PUT", body: JSON.stringify(data) }),

  getUsers: (params?: { page?: number; role?: string; status?: string; domain?: string }) => {
    const query = new URLSearchParams()
    if (params?.page) query.set("page", String(params.page))
    if (params?.role) query.set("role", params.role)
    if (params?.status) query.set("status", params.status)
    if (params?.domain) query.set("domain", params.domain)
    const qs = query.toString()
    return apiFetch<PaginatedUsers>(`/api/admin/users${qs ? `?${qs}` : ""}`)
  },
  updateUser: (id: string, data: { role?: string; status?: string }) =>
    apiFetch<Profile>(`/api/admin/users/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  getDomains: () => apiFetch<Domain[]>("/api/admin/domains"),
  createDomain: (data: { domain: string; activate_existing?: boolean }) =>
    apiFetch<Domain>("/api/admin/domains", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateDomain: (id: string, data: { is_active: boolean }) =>
    apiFetch<Domain>(`/api/admin/domains/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  deleteDomain: (id: string) =>
    apiFetch<void>(`/api/admin/domains/${id}`, { method: "DELETE" }),
}

export interface Profile {
  id: string
  email: string
  full_name: string
  avatar_url: string | null
  role: "admin" | "recruiter" | "employee"
  status: "active" | "pending" | "archived"
  domain: string
  created_at: string
  updated_at: string
}

export interface Domain {
  id: string
  domain: string
  added_by: string | null
  is_active: boolean
  created_at: string
}

export interface PaginatedUsers {
  users: Profile[]
  total: number
  page: number
  per_page: number
}
