"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Nav from "@/components/Nav"
import { api, type Profile, type Domain } from "@/lib/api"

type Tab = "users" | "domains"

export default function AdminPage() {
  const router = useRouter()
  const [profile, setProfile] = useState<Profile | null>(null)
  const [tab, setTab] = useState<Tab>("users")
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .getMe()
      .then((p) => {
        if (p.role !== "admin") {
          router.replace("/dashboard")
          return
        }
        setProfile(p)
        setLoading(false)
      })
      .catch(() => router.replace("/dashboard"))
  }, [router])

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-gray-500">Loading...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Nav profile={profile} />
      <div className="mx-auto max-w-5xl px-6 py-6">
        <div className="flex gap-4 border-b border-gray-200">
          <button
            onClick={() => setTab("users")}
            className={`pb-3 text-sm font-medium ${
              tab === "users"
                ? "border-b-2 border-indigo-600 text-gray-900"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            Users
          </button>
          <button
            onClick={() => setTab("domains")}
            className={`pb-3 text-sm font-medium ${
              tab === "domains"
                ? "border-b-2 border-indigo-600 text-gray-900"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            Domains
          </button>
        </div>

        <div className="mt-6">
          {tab === "users" ? <UsersTab /> : <DomainsTab />}
        </div>
      </div>
    </div>
  )
}

function UsersTab() {
  const [users, setUsers] = useState<Profile[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [roleFilter, setRoleFilter] = useState("")
  const [statusFilter, setStatusFilter] = useState("")
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api
      .getUsers({
        page,
        role: roleFilter || undefined,
        status: statusFilter || undefined,
      })
      .then((data) => {
        setUsers(data.users)
        setTotal(data.total)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [page, roleFilter, statusFilter])

  async function handleUpdateUser(userId: string, updates: { role?: string; status?: string }) {
    const updated = await api.updateUser(userId, updates)
    setUsers((prev) => prev.map((u) => (u.id === userId ? updated : u)))
  }

  return (
    <div>
      <div className="mb-4 flex gap-2">
        <select
          value={roleFilter}
          onChange={(e) => { setRoleFilter(e.target.value); setPage(1) }}
          className="rounded border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700"
        >
          <option value="">All Roles</option>
          <option value="admin">Admin</option>
          <option value="recruiter">Recruiter</option>
          <option value="employee">Employee</option>
        </select>
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }}
          className="rounded border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700"
        >
          <option value="">All Status</option>
          <option value="active">Active</option>
          <option value="pending">Pending</option>
          <option value="archived">Archived</option>
        </select>
      </div>

      {loading ? (
        <p className="text-gray-500">Loading...</p>
      ) : (
        <>
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-gray-500">
                <th className="pb-2 font-medium">User</th>
                <th className="pb-2 font-medium">Domain</th>
                <th className="pb-2 font-medium">Role</th>
                <th className="pb-2 font-medium">Status</th>
                <th className="pb-2 text-right font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id} className="border-b border-gray-100">
                  <td className="py-3">
                    <div className="font-medium text-gray-900">{user.full_name || "\u2014"}</div>
                    <div className="text-xs text-gray-500">{user.email}</div>
                  </td>
                  <td className="py-3 text-gray-600">{user.domain}</td>
                  <td className="py-3">
                    <select
                      value={user.role}
                      onChange={(e) => { void handleUpdateUser(user.id, { role: e.target.value }) }}
                      className="rounded border border-gray-200 bg-white px-2 py-1 text-xs"
                    >
                      <option value="admin">admin</option>
                      <option value="recruiter">recruiter</option>
                      <option value="employee">employee</option>
                    </select>
                  </td>
                  <td className="py-3">
                    <select
                      value={user.status}
                      onChange={(e) => { void handleUpdateUser(user.id, { status: e.target.value }) }}
                      className="rounded border border-gray-200 bg-white px-2 py-1 text-xs"
                    >
                      <option value="active">active</option>
                      <option value="pending">pending</option>
                      <option value="archived">archived</option>
                    </select>
                  </td>
                  <td className="py-3 text-right text-xs text-gray-400">
                    {new Date(user.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="mt-4 flex items-center justify-between text-sm text-gray-500">
            <span>{total} users total</span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="rounded border px-3 py-1 disabled:opacity-50"
              >
                Previous
              </button>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={users.length < 20}
                className="rounded border px-3 py-1 disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

function DomainsTab() {
  const [domains, setDomains] = useState<Domain[]>([])
  const [newDomain, setNewDomain] = useState("")
  const [activateExisting, setActivateExisting] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .getDomains()
      .then((data) => {
        setDomains(data)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault()
    if (!newDomain.trim()) return
    const created = await api.createDomain({
      domain: newDomain.trim().toLowerCase(),
      activate_existing: activateExisting,
    })
    setDomains((prev) => [...prev, created])
    setNewDomain("")
    setActivateExisting(false)
  }

  async function handleToggle(domain: Domain) {
    const updated = await api.updateDomain(domain.id, { is_active: !domain.is_active })
    setDomains((prev) => prev.map((d) => (d.id === domain.id ? updated : d)))
  }

  async function handleDelete(domainId: string) {
    await api.deleteDomain(domainId)
    setDomains((prev) => prev.filter((d) => d.id !== domainId))
  }

  if (loading) return <p className="text-gray-500">Loading...</p>

  return (
    <div>
      <form onSubmit={(e) => { void handleAdd(e) }} className="mb-6 flex items-end gap-3">
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600">Domain</label>
          <input
            type="text"
            value={newDomain}
            onChange={(e) => setNewDomain(e.target.value)}
            placeholder="acme.com"
            className="rounded border border-gray-300 px-3 py-1.5 text-sm"
          />
        </div>
        <label className="flex items-center gap-2 text-sm text-gray-600">
          <input
            type="checkbox"
            checked={activateExisting}
            onChange={(e) => setActivateExisting(e.target.checked)}
          />
          Activate pending users
        </label>
        <button
          type="submit"
          className="rounded bg-indigo-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
        >
          Add Domain
        </button>
      </form>

      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-gray-200 text-gray-500">
            <th className="pb-2 font-medium">Domain</th>
            <th className="pb-2 font-medium">Status</th>
            <th className="pb-2 font-medium">Added</th>
            <th className="pb-2 text-right font-medium">Actions</th>
          </tr>
        </thead>
        <tbody>
          {domains.map((domain) => (
            <tr key={domain.id} className="border-b border-gray-100">
              <td className="py-3 font-medium text-gray-900">{domain.domain}</td>
              <td className="py-3">
                <span
                  className={`rounded px-2 py-0.5 text-xs ${
                    domain.is_active
                      ? "bg-green-100 text-green-800"
                      : "bg-gray-100 text-gray-600"
                  }`}
                >
                  {domain.is_active ? "active" : "disabled"}
                </span>
              </td>
              <td className="py-3 text-gray-500">
                {new Date(domain.created_at).toLocaleDateString()}
              </td>
              <td className="py-3 text-right">
                <button
                  onClick={() => { void handleToggle(domain) }}
                  className="mr-3 text-xs text-indigo-600 hover:underline"
                >
                  {domain.is_active ? "Disable" : "Enable"}
                </button>
                <button
                  onClick={() => { void handleDelete(domain.id) }}
                  className="text-xs text-red-600 hover:underline"
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
