import { Link, Outlet, useRouterState } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  Activity,
  ClipboardList,
  Database,
  FileText,
  LayoutGrid,
  MessageSquare,
  PanelLeftClose,
  PanelLeftOpen,
  ShieldCheck,
  Sparkles,
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

export function DashboardShell() {
  const [collapsed, setCollapsed] = useState(false);
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

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      <aside
        className={cn(
          "flex flex-col bg-sidebar text-sidebar-foreground border-r border-sidebar-border transition-[width] duration-200",
          collapsed ? "w-16" : "w-64",
        )}
      >
        <div className="flex items-center gap-2 px-4 h-16 border-b border-sidebar-border">
          <div className="flex h-9 w-9 items-center justify-center rounded-md bg-sidebar-primary text-sidebar-primary-foreground">
            <ShieldCheck className="h-5 w-5" />
          </div>
          {!collapsed && (
            <div className="leading-tight">
              <div className="text-sm font-semibold">HACCP AI</div>
              <div className="text-[11px] opacity-70">
                FSSAI · Codex compliance
              </div>
            </div>
          )}
        </div>

        {!collapsed && (
          <div className="mx-3 mt-4 rounded-lg bg-sidebar-accent/60 p-3 text-xs">
            <div className="font-medium">Demo FBO Pvt. Ltd.</div>
            <div className="opacity-70">FSSAI Lic. 10012345678901</div>
          </div>
        )}

        <nav className="flex-1 px-2 py-4 space-y-1">
          {NAV.map(({ to, label, icon: Icon }) => {
            const isActive = path.startsWith(to);
            return (
              <Link
                key={to}
                to={to}
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

        <button
          onClick={() => setCollapsed((c) => !c)}
          className="m-3 flex items-center gap-2 rounded-md px-3 py-2 text-xs hover:bg-sidebar-accent/60"
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
        <header className="h-16 border-b border-border bg-card flex items-center justify-between px-6">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <LayoutGrid className="h-4 w-4" />
            <span>Dashboard</span>
            <span className="opacity-50">/</span>
            <span className="text-foreground font-medium">{active}</span>
          </div>
          <div className="flex items-center gap-4">
            {api.useMock && (
              <span className="inline-flex items-center gap-1 text-[11px] px-2 py-1 rounded-full bg-warning/15 text-warning-foreground border border-warning/30">
                <Sparkles className="h-3 w-3" /> Mock data mode
              </span>
            )}
            <span className="inline-flex items-center gap-2 text-xs">
              <span
                className={cn(
                  "h-2 w-2 rounded-full",
                  healthy ? "bg-success" : "bg-destructive",
                )}
              />
              {healthy ? "Backend online" : "Backend offline"}
            </span>
            <div className="h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs font-semibold">
              QA
            </div>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}