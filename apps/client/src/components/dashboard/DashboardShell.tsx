import { Link, Outlet, useRouterState } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  Activity,
  ClipboardList,
  Database,
  FileText,
  LayoutGrid,
  Menu,
  MessageSquare,
  PanelLeftClose,
  PanelLeftOpen,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { api } from "@/lib/haccp/api";

const NAV = [
  { to: "/dashboard/chat", label: "Regulatory Chat", icon: MessageSquare },
  { to: "/dashboard/plan-builder", label: "Plan Builder", icon: ClipboardList },
  { to: "/dashboard/monitor", label: "CCP Monitor", icon: Activity },
  { to: "/dashboard/compliance", label: "Compliance", icon: ShieldCheck },
  { to: "/dashboard/reports", label: "Reports", icon: FileText },
  { to: "/dashboard/knowledge-base", label: "Knowledge Base", icon: Database },
];

function SidebarContent({
  collapsed,
  path,
  onNavClick,
}: {
  collapsed: boolean;
  path: string;
  onNavClick?: () => void;
}) {
  return (
    <>
      <div className="flex items-center gap-2 px-4 h-16 border-b border-sidebar-border shrink-0">
        <div className="flex h-9 w-9 items-center justify-center rounded-md bg-sidebar-primary text-sidebar-primary-foreground shrink-0">
          <ShieldCheck className="h-5 w-5" />
        </div>
        {!collapsed && (
          <div className="leading-tight">
            <div className="text-sm font-semibold">HACCP AI</div>
            <div className="text-[11px] opacity-70">FSSAI · Codex compliance</div>
          </div>
        )}
      </div>

      {!collapsed && (
        <div className="mx-3 mt-4 rounded-lg bg-sidebar-accent/60 p-3 text-xs">
          <div className="font-medium">Demo FBO Pvt. Ltd.</div>
          <div className="opacity-70">FSSAI Lic. 10012345678901</div>
        </div>
      )}

      <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
        {NAV.map(({ to, label, icon: Icon }) => {
          const isActive = path.startsWith(to);
          return (
            <Link
              key={to}
              to={to}
              onClick={onNavClick}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                isActive
                  ? "bg-sidebar-primary text-sidebar-primary-foreground shadow-sm"
                  : "hover:bg-sidebar-accent/60",
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {!collapsed && <span className="truncate">{label}</span>}
            </Link>
          );
        })}
      </nav>
    </>
  );
}

export function DashboardShell() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [healthy, setHealthy] = useState(true);
  const state = useRouterState();
  const path = state.location.pathname;
  const active = NAV.find((n) => path.startsWith(n.to))?.label ?? "Dashboard";

  useEffect(() => {
    api
      .health()
      .then(() => setHealthy(true))
      .catch(() => setHealthy(false));
  }, []);

  // Close mobile drawer on route change
  useEffect(() => {
    setMobileOpen(false);
  }, [path]);

  return (
    <div className="flex min-h-screen bg-background text-foreground relative">
      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Mobile Sidebar Drawer */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex flex-col bg-sidebar text-sidebar-foreground border-r border-sidebar-border w-64 transition-transform duration-200 lg:hidden",
          mobileOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <button
          onClick={() => setMobileOpen(false)}
          className="absolute right-3 top-4 p-1.5 rounded-md hover:bg-sidebar-accent/60"
          aria-label="Close navigation"
        >
          <X className="h-4 w-4" />
        </button>
        <SidebarContent
          collapsed={false}
          path={path}
          onNavClick={() => setMobileOpen(false)}
        />
      </aside>

      {/* Desktop Sidebar */}
      <aside
        className={cn(
          "hidden lg:flex flex-col bg-sidebar text-sidebar-foreground border-r border-sidebar-border transition-[width] duration-200 shrink-0",
          collapsed ? "w-16" : "w-64",
        )}
      >
        <SidebarContent collapsed={collapsed} path={path} />

        <button
          onClick={() => setCollapsed((c) => !c)}
          className="m-3 flex items-center gap-2 rounded-md px-3 py-2 text-xs hover:bg-sidebar-accent/60"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? (
            <PanelLeftOpen className="h-4 w-4" />
          ) : (
            <>
              <PanelLeftClose className="h-4 w-4" /> Collapse
            </>
          )}
        </button>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 border-b border-border bg-card flex items-center justify-between px-4 lg:px-6 shrink-0">
          {/* Mobile hamburger */}
          <button
            className="lg:hidden p-2 rounded-md hover:bg-muted transition-colors"
            onClick={() => setMobileOpen(true)}
            aria-label="Open navigation"
            id="mobile-menu-btn"
          >
            <Menu className="h-5 w-5" />
          </button>

          <div className="hidden lg:flex items-center gap-2 text-sm text-muted-foreground">
            <LayoutGrid className="h-4 w-4" />
            <span>Dashboard</span>
            <span className="opacity-50">/</span>
            <span className="text-foreground font-medium">{active}</span>
          </div>

          {/* Mobile: show active page name */}
          <div className="lg:hidden text-sm font-medium">{active}</div>

          <div className="flex items-center gap-3">
            {api.useMock && (
              <span className="hidden sm:inline-flex items-center gap-1 text-[11px] px-2 py-1 rounded-full bg-warning/15 text-warning-foreground border border-warning/30">
                <Sparkles className="h-3 w-3" /> Mock
              </span>
            )}
            <span className="inline-flex items-center gap-2 text-xs">
              <span
                className={cn(
                  "h-2 w-2 rounded-full",
                  healthy ? "bg-success" : "bg-destructive",
                )}
              />
              <span className="hidden sm:inline">
                {healthy ? "Backend online" : "Backend offline"}
              </span>
            </span>
            <div className="h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs font-semibold shrink-0">
              QA
            </div>
          </div>
        </header>

        {/* Mobile bottom nav */}
        <div className="lg:hidden fixed bottom-0 inset-x-0 z-30 bg-card border-t border-border flex items-center justify-around px-2 py-1 safe-area-inset-bottom">
          {NAV.slice(0, 5).map(({ to, label, icon: Icon }) => {
            const isActive = path.startsWith(to);
            return (
              <Link
                key={to}
                to={to}
                className={cn(
                  "flex flex-col items-center gap-0.5 px-2 py-1.5 rounded-lg min-w-0 text-[10px] transition-colors",
                  isActive
                    ? "text-primary"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                <Icon className="h-5 w-5 shrink-0" />
                <span className="truncate">{label.split(" ")[0]}</span>
              </Link>
            );
          })}
        </div>

        <main className="flex-1 overflow-y-auto p-4 lg:p-6 pb-20 lg:pb-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}