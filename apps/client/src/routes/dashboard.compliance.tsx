import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  AlertOctagon,
  ShieldCheck,
  AlertTriangle,
  Loader2,
  RefreshCw,
  CheckCircle2,
  Clock,
} from "lucide-react";
import { api } from "@/lib/haccp/api";
import type { ComplianceAlert } from "@/lib/haccp/types";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Timeline, type TimelineItem } from "@/components/ui/Timeline";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/dashboard/compliance")({
  component: CompliancePage,
});

function CompliancePage() {
  const [plans, setPlans] = useState<any[]>([]);
  const [planId, setPlanId] = useState<string>("");
  const [score, setScore] = useState(0);
  const [alerts, setAlerts] = useState<ComplianceAlert[]>([]);
  const [globalAlerts, setGlobalAlerts] = useState<any[]>([]);
  const [sections, setSections] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState<string | null>(null);

  // 1. Fetch plans on mount
  useEffect(() => {
    async function loadPlans() {
      setLoading(true);
      try {
        const list = await api.listPlans();
        setPlans(list);
        if (list.length > 0) {
          setPlanId(list[0].plan_id);
        }
      } catch (e) {
        console.error("Failed to load plans:", e);
      } finally {
        setLoading(false);
      }
    }
    loadPlans();
    loadGlobalAlerts();
  }, []);

  async function loadGlobalAlerts() {
    try {
      const res = await api.complianceAlertsFeed();
      setGlobalAlerts(res.alerts);
    } catch (e) {
      console.error("Failed to load global alerts:", e);
    }
  }

  // 2. Fetch compliance data when planId changes
  useEffect(() => {
    if (!planId) return;
    async function loadComplianceData() {
      setLoading(true);
      try {
        const r = await api.alerts(planId);
        setScore(r.compliance_score);
        setAlerts(r.alerts);
        if (r.sections) {
          setSections(r.sections);
        }
      } catch (e) {
        console.error("Failed to load compliance data:", e);
      } finally {
        setLoading(false);
      }
    }
    loadComplianceData();
  }, [planId]);

  async function handleScan() {
    setScanning(true);
    setScanResult(null);
    try {
      const res = await api.regulatoryCheck();
      setScanResult(
        `Scan complete: ${res.plans_scanned} plan(s) checked, ${res.alerts_created} new alert(s) generated.`
      );
      await loadGlobalAlerts();
    } catch (e) {
      setScanResult("Scan failed: " + (e as Error).message);
    } finally {
      setScanning(false);
    }
  }

  // Build timeline items from global alerts
  const timelineItems: TimelineItem[] = globalAlerts.map((a) => ({
    id: a.id,
    date: a.created_at
      ? new Date(a.created_at).toLocaleDateString("en-IN", {
          day: "numeric",
          month: "short",
          year: "numeric",
        })
      : "—",
    title: `${a.regulatory_source}: ${a.change_summary.slice(0, 60)}${a.change_summary.length > 60 ? "…" : ""}`,
    description: `Affects: ${(a.affected_sections || []).join(", ")}`,
    badge: a.regulatory_source,
    badgeVariant:
      a.regulatory_source === "FSSAI"
        ? "warning"
        : a.regulatory_source === "Codex"
        ? "default"
        : "success",
  }));

  if (loading && plans.length === 0) {
    return (
      <div className="h-[400px] flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (plans.length === 0) {
    return (
      <div className="h-[400px] flex flex-col items-center justify-center text-center p-6 bg-card rounded-xl border border-border">
        <AlertTriangle className="h-12 w-12 text-warning-foreground mb-4" />
        <h3 className="font-semibold text-lg">No active plans found</h3>
        <p className="text-sm text-muted-foreground max-w-sm mt-1">
          Please complete your first plan in the Plan Builder before accessing compliance checklists.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-primary to-teal-500 bg-clip-text text-transparent">
            Regulatory Compliance Monitor
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            FSSAI Schedule 4 audit readiness and proactive regulatory change surveillance.
          </p>
        </div>
        <Button
          variant="outline"
          disabled={scanning}
          onClick={handleScan}
          className="gap-2 cursor-pointer"
          id="regulatory-scan-btn"
        >
          {scanning ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
          {scanning ? "Scanning…" : "Run Regulatory Scan"}
        </Button>
      </div>

      {/* Scan result banner */}
      {scanResult && (
        <div
          className={cn(
            "rounded-xl border p-4 text-sm flex items-start gap-2 animate-in slide-in-from-top-4 duration-300",
            scanResult.includes("failed")
              ? "border-destructive/30 bg-destructive/5 text-destructive"
              : "border-success/30 bg-success/5 text-success"
          )}
        >
          {scanResult.includes("failed") ? (
            <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
          ) : (
            <CheckCircle2 className="h-4 w-4 shrink-0 mt-0.5" />
          )}
          {scanResult}
        </div>
      )}

      {/* Plan Selector */}
      <div className="flex items-center gap-4 bg-card p-4 rounded-xl border border-border">
        <label className="text-sm font-medium text-muted-foreground">Select Plan:</label>
        <Select value={planId} onValueChange={setPlanId}>
          <SelectTrigger className="w-72 bg-background border-border">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {plans.map((p) => (
              <SelectItem key={p.plan_id} value={p.plan_id}>
                {p.business_name} ({p.product_category})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="grid lg:grid-cols-[320px_1fr] gap-6">
        {/* Compliance Score Gauge */}
        <div className="rounded-xl border border-border bg-card p-6 flex flex-col items-center">
          <div className="text-sm text-muted-foreground">FSSAI compliance score</div>
          <Gauge value={score} />
          <div className="mt-3 text-xs text-muted-foreground flex items-center gap-1">
            <ShieldCheck className="h-3 w-3 text-success" /> Schedule 4 audit readiness
          </div>

          {/* Score breakdown legend */}
          <div className="mt-4 w-full space-y-1.5">
            {[
              { label: "Excellent", range: "≥90%", color: "bg-success" },
              { label: "Good", range: "70–89%", color: "bg-teal-500" },
              { label: "Needs Action", range: "50–69%", color: "bg-warning-foreground" },
              { label: "Non-compliant", range: "<50%", color: "bg-destructive" },
            ].map((item) => (
              <div key={item.label} className="flex items-center gap-2 text-xs text-muted-foreground">
                <div className={cn("h-2 w-2 rounded-full", item.color)} />
                <span className="font-medium">{item.label}</span>
                <span className="ml-auto">{item.range}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Section Coverage Accordion */}
        <div className="rounded-xl border border-border bg-card p-5">
          <h3 className="font-semibold">Section coverage</h3>
          {sections.length > 0 ? (
            <Accordion type="multiple" className="mt-3">
              {sections.map((s) => (
                <AccordionItem key={s.title} value={s.title}>
                  <AccordionTrigger className="text-sm">
                    <span className="flex items-center gap-2">
                      {s.items.every(([, ok]: [string, boolean]) => ok) ? (
                        <CheckCircle2 className="h-3.5 w-3.5 text-success shrink-0" />
                      ) : (
                        <AlertTriangle className="h-3.5 w-3.5 text-warning-foreground shrink-0" />
                      )}
                      {s.title}
                    </span>
                  </AccordionTrigger>
                  <AccordionContent>
                    <ul className="text-sm space-y-1">
                      {s.items.map(([label, ok]: [string, boolean]) => (
                        <li
                          key={label}
                          className="flex items-center justify-between border-b border-border py-1 last:border-0"
                        >
                          <span>{label}</span>
                          <span
                            className={
                              ok
                                ? "text-success text-xs font-medium"
                                : "text-warning-foreground text-xs font-medium"
                            }
                          >
                            {ok ? "✓ YES" : "⚠ ACTION"}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          ) : (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <ShieldCheck className="h-10 w-10 text-muted-foreground mb-2 opacity-40" />
              <p className="text-sm text-muted-foreground">
                No section coverage data yet. Complete the plan to see detailed compliance breakdown.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Two-column: Regulatory change feed + Amendment History Timeline */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Regulatory Alert Feed */}
        <div className="rounded-xl border border-border bg-card p-5">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <AlertOctagon className="h-4 w-4 text-warning-foreground" />
            Regulatory change feed
            {alerts.length > 0 && (
              <span className="ml-auto text-xs px-2 py-0.5 rounded-full bg-warning/10 text-warning-foreground border border-warning/20">
                {alerts.length} alert{alerts.length !== 1 ? "s" : ""}
              </span>
            )}
          </h3>
          <div className="space-y-3">
            {alerts.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <CheckCircle2 className="h-10 w-10 text-success mb-2 opacity-60" />
                <p className="text-sm text-muted-foreground">No regulatory alerts for this plan.</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Run a regulatory scan to check for updates.
                </p>
              </div>
            ) : (
              alerts.map((a) => (
                <div
                  key={a.id}
                  className="rounded-lg border border-warning/30 bg-warning/5 p-4 transition-all hover:border-warning/50"
                >
                  <div className="flex items-start gap-3">
                    <AlertOctagon className="h-5 w-5 text-warning-foreground shrink-0" />
                    <div className="flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-warning/20 text-warning-foreground border border-warning/30">
                          {a.regulatory_source}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {new Date(a.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <p className="mt-2 text-sm">{a.change_summary}</p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        Affects: {a.affected_sections.join(", ")}
                      </p>
                    </div>
                    <Button size="sm" variant="outline">
                      Update plan
                    </Button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Amendment History Timeline */}
        <div className="rounded-xl border border-border bg-card p-5">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Clock className="h-4 w-4 text-primary" />
            Amendment history
            <span className="ml-auto text-xs text-muted-foreground">
              {globalAlerts.length} event{globalAlerts.length !== 1 ? "s" : ""}
            </span>
          </h3>
          <Timeline items={timelineItems} />
        </div>
      </div>
    </div>
  );
}

function Gauge({ value }: { value: number }) {
  const r = 56;
  const c = 2 * Math.PI * r;
  const offset = c - (value / 100) * c;
  const color =
    value >= 90
      ? "var(--color-success)"
      : value >= 70
      ? "var(--color-teal-500, #14b8a6)"
      : value >= 50
      ? "var(--color-warning-foreground)"
      : "var(--color-destructive)";
  return (
    <svg width="160" height="160" viewBox="0 0 140 140" className="mt-4">
      <circle cx="70" cy="70" r={r} stroke="var(--color-muted)" strokeWidth="12" fill="none" />
      <circle
        cx="70"
        cy="70"
        r={r}
        stroke={color}
        strokeWidth="12"
        fill="none"
        strokeDasharray={c}
        strokeDashoffset={offset}
        strokeLinecap="round"
        transform="rotate(-90 70 70)"
        style={{ transition: "stroke-dashoffset 600ms ease, stroke 400ms ease" }}
      />
      <text
        x="70"
        y="70"
        textAnchor="middle"
        fontSize="26"
        fontWeight="700"
        fill="var(--color-foreground)"
        dy="0.35em"
      >
        {value}%
      </text>
    </svg>
  );
}