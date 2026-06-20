import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { FileText, Link2Off, LogOut, Search, ShieldCheck } from "lucide-react";

export default function TopNavbar() {
  const location = useLocation();
  const [loggingOut, setLoggingOut] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);

  const navItems = [
    { label: "AI Search", path: "/search", icon: Search },
    { label: "Documents", path: "/documents", icon: FileText },
  ];

  const handleLogout = async () => {
    try {
      setLoggingOut(true);
      await fetch("http://localhost:8000/api/auth/logout", {
        credentials: "include",
      });
      window.location.href = "/";
    } catch (error) {
      console.error(error);
      setLoggingOut(false);
    }
  };

  const handleDisconnect = async () => {
    const confirmed = window.confirm(
      "Disconnect Google and remove all synced documents and emails from this system? You will need to sign in again next time."
    );

    if (!confirmed) return;

    try {
      setDisconnecting(true);
      await fetch("http://localhost:8000/api/auth/disconnect", {
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
        <div className="flex min-w-0 items-center gap-6 lg:gap-10">
          <Link to="/search" className="flex min-w-0 items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#A61E22] text-sm font-black text-white shadow-md shadow-[#A61E22]/20">
              R
            </div>
            <div className="min-w-0">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[#A61E22]">
                RIIDL
              </p>
              <h1 className="truncate text-sm font-semibold text-zinc-950 sm:text-base">
                Enterprise KMS
              </h1>
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

        <div className="flex items-center gap-2 sm:gap-3">
          <div className="hidden items-center gap-2 rounded-full border border-zinc-200 bg-white px-3 py-2 text-xs font-medium text-zinc-600 lg:flex">
            <ShieldCheck size={14} className="text-[#A61E22]" />
            Secure workspace
          </div>
          <button
            onClick={handleDisconnect}
            disabled={disconnecting || loggingOut}
            className="inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-red-200 bg-red-50 px-3 text-sm font-semibold text-red-700 shadow-sm transition hover:border-red-300 hover:bg-red-100 disabled:opacity-50"
            title="Disconnect Google"
          >
            <Link2Off size={16} />
            <span className="hidden xl:inline">{disconnecting ? "Disconnecting" : "Disconnect Google"}</span>
          </button>
          <button
            onClick={handleLogout}
            disabled={loggingOut || disconnecting}
            className="inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-zinc-200 bg-white px-3 text-sm font-semibold text-zinc-700 shadow-sm transition hover:border-[#A61E22]/30 hover:text-[#A61E22] disabled:opacity-50"
            title="Logout"
          >
            <LogOut size={16} />
            <span className="hidden sm:inline">{loggingOut ? "Logging out" : "Logout"}</span>
          </button>
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-zinc-950 text-sm font-semibold text-white shadow-sm">
            S
          </div>
        </div>
      </div>
    </header>
  );
}
