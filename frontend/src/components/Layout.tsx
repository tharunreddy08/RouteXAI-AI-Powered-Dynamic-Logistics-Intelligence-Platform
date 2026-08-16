import { NavLink, Outlet } from "react-router-dom";
import {
  LayoutDashboard,
  Package,
  PlusSquare,
  Map as MapIcon,
  Radio,
  BarChart3,
  Leaf,
  Users,
  History,
  LogOut,
  Zap,
} from "lucide-react";
import { useAuth } from "../lib/auth";
import type { UserRole } from "../lib/types";

interface NavItem {
  to: string;
  label: string;
  icon: React.ReactNode;
  roles?: UserRole[];
}

const NAV: NavItem[] = [
  { to: "/", label: "Dashboard", icon: <LayoutDashboard size={17} /> },
  { to: "/orders", label: "Orders", icon: <Package size={17} />, roles: ["admin", "dispatcher"] },
  { to: "/orders/new", label: "Manual Order Entry", icon: <PlusSquare size={17} />, roles: ["admin", "dispatcher"] },
  { to: "/fleet", label: "Fleet & Map", icon: <MapIcon size={17} /> },
  { to: "/hardware", label: "Hardware Demo", icon: <Radio size={17} />, roles: ["admin", "dispatcher"] },
  { to: "/analytics", label: "Analysis", icon: <BarChart3 size={17} /> },
  { to: "/riders", label: "Rider Performance", icon: <Users size={17} />, roles: ["admin", "dispatcher"] },
  { to: "/route-history", label: "Route History", icon: <History size={17} /> },
];

export default function Layout() {
  const { user, logout } = useAuth();

  const visibleNav = NAV.filter((item) => !item.roles || (user && item.roles.includes(user.role)));

  return (
    <div className="min-h-screen flex bg-base-950 bg-grid-fade">
      {/* Sidebar */}
      <aside className="w-60 shrink-0 border-r border-panelBorder bg-base-900/60 backdrop-blur flex flex-col">
        <div className="h-16 flex items-center gap-2 px-5 border-b border-panelBorder">
          <div className="w-7 h-7 rounded-md bg-signal/15 border border-signal/40 flex items-center justify-center">
            <Zap size={15} className="text-signal" />
          </div>
          <span className="font-display font-semibold tracking-tight text-ink">RouteXAI</span>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {visibleNav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors ${
                  isActive
                    ? "bg-signal/10 text-signal border border-signal/25"
                    : "text-ink-dim hover:text-ink hover:bg-base-800 border border-transparent"
                }`
              }
            >
              {item.icon}
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="p-3 border-t border-panelBorder">
          <div className="flex items-center gap-2 px-2 py-2 rounded-lg">
            <div className="w-8 h-8 rounded-full bg-base-700 flex items-center justify-center text-xs font-mono text-ink-dim">
              {user?.name?.slice(0, 2).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm text-ink truncate">{user?.name}</div>
              <div className="text-xs text-ink-faint capitalize">{user?.role}</div>
            </div>
            <button
              onClick={logout}
              className="text-ink-faint hover:text-status-danger transition-colors"
              title="Log out"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 border-b border-panelBorder flex items-center justify-between px-6 bg-base-900/40 backdrop-blur">
          <div className="flex items-center gap-2 text-xs font-mono text-ink-faint">
            <span className="w-1.5 h-1.5 rounded-full bg-signal animate-pulseDot" />
            LIVE — AI-POWERED DYNAMIC LOGISTICS INTELLIGENCE
          </div>
          <div className="flex items-center gap-4 text-xs text-ink-faint font-mono">
            <span className="flex items-center gap-1">
              <BarChart3 size={13} /> OR-Tools VRPTW
            </span>
            <span className="flex items-center gap-1">
              <Leaf size={13} /> Sustainability Tracking
            </span>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>

        <footer className="border-t border-panelBorder px-6 py-3 text-xs text-ink-faint font-mono">
          RouteXAI – AI-Powered Dynamic Logistics Intelligence Platform
        </footer>
      </div>
    </div>
  );
}
