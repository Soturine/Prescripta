import { LogOut } from "lucide-react";
import { Outlet } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { formatRole } from "../utils/formatters";
import Sidebar from "./Sidebar";

export default function Layout() {
  const { logout, user } = useAuth();

  return (
    <div className="min-h-screen text-ink lg:flex">
      <Sidebar />
      <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
        <div className="mx-auto w-full max-w-7xl">
          <div className="mb-6 flex flex-col gap-3 rounded-lg border border-slate-200 bg-white/95 px-4 py-3 shadow-sm backdrop-blur sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm font-bold text-ink">{user?.name}</p>
              <p className="text-xs text-slate-500">
                {user?.email} · {formatRole(user?.role)}
              </p>
            </div>
            <button className="btn-secondary w-fit" onClick={logout} title="Sair" type="button">
              <LogOut aria-hidden="true" className="h-4 w-4" />
              Sair
            </button>
          </div>
          <Outlet />
        </div>
      </main>
    </div>
  );
}
