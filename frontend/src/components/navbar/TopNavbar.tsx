import { useEffect, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { FileText, Link2Off, LogOut, Search, ShieldCheck } from "lucide-react";
import { API_URL } from "../../services/api.ts";

interface UserInfo {
  email: string | null;
  name: string | null;
}

export default function TopNavbar() {
  const location = useLocation();
  const [loggingOut, setLoggingOut] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [user, setUser] = useState<UserInfo>({ email: null, name: null });
  const dropdownRef = useRef<HTMLDivElement>(null);

  const navItems = [
    { label: "AI Search", path: "/search", icon: Search },
    { label: "Documents", path: "/documents", icon: FileText },
  ];

  useEffect(() => {
    fetch(`${API_URL}/api/auth/me`, { credentials: "include" })
      .then((r) => r.json())
      .then((data) => {
        setUser({ email: data.email ?? null, name: data.name ?? null });
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const initial = (user.name?.[0] ?? user.email?.[0] ?? "?").toUpperCase();

  const handleLogout = async () => {
    try {
      setLoggingOut(true);
      setDropdownOpen(false);
      await fetch(`${API_URL}/api/auth/logout`, {
        method: "GET",
        credentials: "include",
      });
      localStorage.clear();
      sessionStorage.clear();
      window.location.href = "/";
    } catch (error) {
      console.error(error);
      setLoggingOut(false);
    }
  };

  const handleDisconnect = async () => {
    setDropdownOpen(false);
    const confirmed = window.confirm(
      "Disconnect Google from RIIDL KMS?\n\nYour synced documents and emails will remain in the knowledge base. Only your Google account connection will be removed."
    );
    if (!confirmed) return;

    try {
      setDisconnecting(true);
      await fetch(`${API_URL}/api/auth/disconnect`, {
        method: "POST",
        credentials: "include",
      });
      window.location.href = "/";
    } catch (error) {
      console.error(error);
      setDisconnecting(false);
    }
  };

  return (
    <header className="h-[72px] border-b border-zinc-200 bg-white/92 text-zinc-950 shadow-sm backdrop-blur">
      <div className="flex h-full items-center justify-between px-5 md:px-8">

        {/* ── Left: logo + nav ─────────────────────────────────────── */}
        <div className="flex min-w-0 items-center gap-6 lg:gap-10">
          <Link to="/search" className="flex min-w-0 items-center gap-3">
            <img src="/riidl_logo.png" alt="RIIDL" className="h-12 w-auto" />
            <div className="min-w-0">
              <h1 className="truncate text-sm font-semibold text-zinc-950 sm:text-base" />
            </div>
          </Link>

          <nav className="flex items-center gap-1 rounded-lg border border-zinc-200 bg-zinc-50 p-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition ${
                    active
                      ? "bg-white text-[#A61E22] shadow-sm"
                      : "text-zinc-600 hover:bg-white hover:text-zinc-950"
                  }`}
                >
                  <Icon size={16} />
                  <span className="hidden sm:inline">{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* ── Right: secure badge + avatar dropdown ────────────────── */}
        <div className="flex items-center gap-2 sm:gap-3">
          <div className="hidden items-center gap-2 rounded-full border border-zinc-200 bg-white px-3 py-2 text-xs font-medium text-zinc-600 lg:flex">
            <ShieldCheck size={14} className="text-[#A61E22]" />
            Secure workspace
          </div>

          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setDropdownOpen((prev) => !prev)}
              disabled={loggingOut || disconnecting}
              className="flex h-10 w-10 items-center justify-center rounded-full bg-zinc-950 text-sm font-semibold text-white shadow-sm transition hover:bg-zinc-700 disabled:opacity-50"
              title="Account"
            >
              {initial}
            </button>

            {dropdownOpen && (
              <div className="absolute right-0 top-12 z-50 w-64 rounded-xl border border-zinc-200 bg-white shadow-lg">

                <div className="border-b border-zinc-100 px-4 py-3">
                  <p className="text-xs font-medium text-zinc-400 uppercase tracking-wide mb-1">
                    Signed in as
                  </p>
                  <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-zinc-950 text-sm font-semibold text-white">
                      {initial}
                    </div>
                    <div className="min-w-0">
                      {user.name && (
                        <p className="truncate text-sm font-semibold text-zinc-900">
                          {user.name}
                        </p>
                      )}
                      <p className="truncate text-xs text-zinc-500">
                        {user.email ?? "Loading…"}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="p-2 flex flex-col gap-1">
                  <button
                    onClick={handleLogout}
                    disabled={loggingOut || disconnecting}
                    className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-zinc-700 transition hover:bg-zinc-50 hover:text-zinc-950 disabled:opacity-50"
                  >
                    <LogOut size={16} className="shrink-0 text-zinc-400" />
                    {loggingOut ? "Logging out…" : "Logout"}
                  </button>

                  <button
                    onClick={handleDisconnect}
                    disabled={disconnecting || loggingOut}
                    className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-red-600 transition hover:bg-red-50 disabled:opacity-50"
                  >
                    <Link2Off size={16} className="shrink-0" />
                    {disconnecting ? "Disconnecting…" : "Disconnect Google"}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

      </div>
    </header>
  );
}
