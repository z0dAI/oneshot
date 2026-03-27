"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { api, APIError } from "@/lib/api";
import { Nav } from "@/components/Nav";
import { AdminUserTable } from "@/components/AdminUserTable";
import type { Profile, Domain } from "@/lib/api";

function DomainsTab() {
  const [domains, setDomains] = useState<Domain[]>([]);
  const [newDomain, setNewDomain] = useState("");
  const [activateExisting, setActivateExisting] = useState(false);

  const loadDomains = useCallback(() => {
    api.getDomains().then(setDomains);
  }, []);

  useEffect(() => {
    loadDomains();
  }, [loadDomains]);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDomain.trim()) return;
    await api.addDomain({
      domain: newDomain.trim(),
      activate_existing: activateExisting,
    });
    setNewDomain("");
    setActivateExisting(false);
    loadDomains();
  };

  const handleToggle = async (domain: Domain) => {
    await api.updateDomain(domain.id, { is_active: !domain.is_active });
    loadDomains();
  };

  const handleDelete = async (domain: Domain) => {
    if (!confirm(`Delete domain "${domain.domain}"?`)) return;
    await api.deleteDomain(domain.id);
    loadDomains();
  };

  return (
    <div>
      {/* Add domain form */}
      <form onSubmit={handleAdd} className="flex gap-3 mb-6">
        <input
          type="text"
          value={newDomain}
          onChange={(e) => setNewDomain(e.target.value)}
          placeholder="acme.com"
          className="border border-gray-300 rounded px-3 py-1.5 text-sm flex-1"
        />
        <label className="flex items-center gap-1 text-sm text-gray-600">
          <input
            type="checkbox"
            checked={activateExisting}
            onChange={(e) => setActivateExisting(e.target.checked)}
          />
          Activate pending users
        </label>
        <button
          type="submit"
          className="px-4 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
        >
          Add Domain
        </button>
      </form>

      {/* Domain list */}
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b border-gray-200 text-left text-sm text-gray-500">
            <th className="pb-2 font-medium">Domain</th>
            <th className="pb-2 font-medium">Status</th>
            <th className="pb-2 font-medium">Added</th>
            <th className="pb-2 font-medium">Actions</th>
          </tr>
        </thead>
        <tbody>
          {domains.map((d) => (
            <tr key={d.id} className="border-b border-gray-100 text-sm">
              <td className="py-2">{d.domain}</td>
              <td className="py-2">
                <span
                  className={`px-2 py-0.5 rounded text-xs ${d.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}
                >
                  {d.is_active ? "Active" : "Disabled"}
                </span>
              </td>
              <td className="py-2 text-gray-400">
                {new Date(d.created_at).toLocaleDateString()}
              </td>
              <td className="py-2 flex gap-3">
                <button
                  onClick={() => handleToggle(d)}
                  className="text-sm text-blue-600 hover:underline"
                >
                  {d.is_active ? "Disable" : "Enable"}
                </button>
                <button
                  onClick={() => handleDelete(d)}
                  className="text-sm text-red-600 hover:underline"
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
          {domains.length === 0 && (
            <tr>
              <td colSpan={4} className="py-4 text-center text-gray-400 text-sm">
                No domains configured yet.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

export default function AdminPageClient() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [tab, setTab] = useState<"users" | "domains">("users");
  const router = useRouter();

  useEffect(() => {
    api
      .getMe()
      .then((p) => {
        if (p.role !== "admin") {
          router.push("/dashboard");
          return;
        }
        setProfile(p);
      })
      .catch((err: unknown) => {
        if (err instanceof APIError && err.status === 401) {
          router.push("/");
        }
      });
  }, [router]);

  if (!profile) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-500">
        Loading...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Nav profile={profile} />
      <main className="max-w-6xl mx-auto py-8 px-4">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Admin Panel</h1>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 border-b border-gray-200">
          <button
            onClick={() => setTab("users")}
            className={`px-4 py-2 text-sm font-medium -mb-px ${
              tab === "users"
                ? "border-b-2 border-blue-600 text-blue-600"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            Users
          </button>
          <button
            onClick={() => setTab("domains")}
            className={`px-4 py-2 text-sm font-medium -mb-px ${
              tab === "domains"
                ? "border-b-2 border-blue-600 text-blue-600"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            Domains
          </button>
        </div>

        {/* Tab content */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          {tab === "users" ? <AdminUserTable /> : <DomainsTab />}
        </div>
      </main>
    </div>
  );
}
