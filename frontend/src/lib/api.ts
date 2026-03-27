import { createClient } from "./supabase/client";
import { API_URL } from "./config";

export class APIError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

async function fetchAPI<T = unknown>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(session?.access_token && {
        Authorization: `Bearer ${session.access_token}`,
      }),
      ...options.headers,
    },
  });

  if (!res.ok) {
    const text = await res.text();
    throw new APIError(res.status, text);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export type Profile = {
  id: string;
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  role: "admin" | "recruiter" | "employee";
  status: "active" | "pending" | "archived";
  domain: string;
  created_at: string;
  updated_at: string;
};

export type PaginatedUsers = {
  users: Profile[];
  total: number;
  page: number;
  per_page: number;
};

export type Domain = {
  id: string;
  domain: string;
  added_by: string | null;
  is_active: boolean;
  created_at: string;
};

export const api = {
  getMe: () => fetchAPI<Profile>("/api/me"),

  updateMe: (data: { full_name?: string; avatar_url?: string }) =>
    fetchAPI<Profile>("/api/me", { method: "PUT", body: JSON.stringify(data) }),

  getUsers: (params?: { role?: string; status?: string; page?: number }) => {
    const sp = new URLSearchParams();
    if (params?.role) sp.set("role", params.role);
    if (params?.status) sp.set("status", params.status);
    if (params?.page) sp.set("page", String(params.page));
    const qs = sp.toString();
    return fetchAPI<PaginatedUsers>(`/api/admin/users${qs ? `?${qs}` : ""}`);
  },

  updateUser: (id: string, data: { role?: string; status?: string }) =>
    fetchAPI<Profile>(`/api/admin/users/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  getDomains: () => fetchAPI<Domain[]>("/api/admin/domains"),

  addDomain: (data: { domain: string; activate_existing?: boolean }) =>
    fetchAPI<Domain>("/api/admin/domains", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateDomain: (id: string, data: { is_active: boolean }) =>
    fetchAPI<Domain>(`/api/admin/domains/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  deleteDomain: (id: string) =>
    fetchAPI<void>(`/api/admin/domains/${id}`, { method: "DELETE" }),
};
