import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

export interface TimelineItem {
  id: string;
  date: string;
  title: string;
  description?: string;
  badge?: string;
  badgeVariant?: "default" | "warning" | "success" | "destructive";
  icon?: ReactNode;
}

interface TimelineProps {
  items: TimelineItem[];
  className?: string;
}

const badgeClasses: Record<NonNullable<TimelineItem["badgeVariant"]>, string> = {
  default: "bg-primary/10 text-primary border-primary/20",
  warning: "bg-warning/10 text-warning-foreground border-warning/30",
  success: "bg-success/10 text-success border-success/30",
  destructive: "bg-destructive/10 text-destructive border-destructive/30",
};

export function Timeline({ items, className }: TimelineProps) {
  if (!items || items.length === 0) {
    return (
      <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">
        No history to display.
      </div>
    );
  }

  return (
    <div className={cn("relative pl-4", className)}>
      {/* Vertical line */}
      <div className="absolute left-[1.05rem] top-3 bottom-3 w-px bg-border" />

      <div className="space-y-5">
        {items.map((item, idx) => (
          <div
            key={item.id}
            className="relative flex gap-3 animate-in fade-in slide-in-from-left-2 duration-300"
            style={{ animationDelay: `${idx * 60}ms`, animationFillMode: "both" }}
          >
            {/* Dot */}
            <div
              className={cn(
                "relative z-10 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 bg-background transition-colors",
                item.badgeVariant === "destructive"
                  ? "border-destructive"
                  : item.badgeVariant === "warning"
                  ? "border-warning-foreground"
                  : item.badgeVariant === "success"
                  ? "border-success"
                  : "border-primary",
              )}
            >
              {item.icon ? (
                <span className="text-[10px]">{item.icon}</span>
              ) : (
                <div
                  className={cn(
                    "h-2 w-2 rounded-full",
                    item.badgeVariant === "destructive"
                      ? "bg-destructive"
                      : item.badgeVariant === "warning"
                      ? "bg-warning-foreground"
                      : item.badgeVariant === "success"
                      ? "bg-success"
                      : "bg-primary",
                  )}
                />
              )}
            </div>

            {/* Content */}
            <div className="flex-1 pb-1">
              <div className="flex flex-wrap items-start gap-2 mb-0.5">
                <span className="text-sm font-semibold text-foreground leading-tight">
                  {item.title}
                </span>
                {item.badge && (
                  <span
                    className={cn(
                      "inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium border uppercase tracking-wider",
                      badgeClasses[item.badgeVariant ?? "default"],
                    )}
                  >
                    {item.badge}
                  </span>
                )}
              </div>
              {item.description && (
                <p className="text-xs text-muted-foreground leading-relaxed mt-0.5 max-w-xl">
                  {item.description}
                </p>
              )}
              <time className="text-[10px] text-muted-foreground/60 mt-1 block">
                {item.date}
              </time>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
