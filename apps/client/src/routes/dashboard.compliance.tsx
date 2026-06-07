import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { AlertOctagon, ShieldCheck, AlertTriangle, Loader2 } from "lucide-react";
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

export const Route = createFileRoute("/dashboard/compliance")({
  component: CompliancePage,
});

function CompliancePage() {
  const [plans, setPlans] = useState<any[]>([]);
  const [planId, setPlanId] = useState<string>("");
  const [score, setScore] = useState(0);
  const [alerts, setAlerts] = useState<ComplianceAlert[]>([]);
  const [sections, setSections] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

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
  }, []);

  // 2. Fetch compliance alerts and checklist items when planId changes
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
    <div className="space-y-6">
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
        <div className="rounded-xl border border-border bg-card p-6 flex flex-col items-center">
          <div className="text-sm text-muted-foreground">
            FSSAI compliance score
          </div>
          <Gauge value={score} />
          <div className="mt-3 text-xs text-muted-foreground flex items-center gap-1">
            <ShieldCheck className="h-3 w-3 text-success" /> Schedule 4 audit
            readiness
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card p-5">
          <h3 className="font-semibold">Section coverage</h3>
          <Accordion type="multiple" className="mt-3">
            {sections.map((s) => (
              <AccordionItem key={s.title} value={s.title}>
                <AccordionTrigger className="text-sm">
                  {s.title}
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
                          {ok ? "YES" : "ACTION"}
                        </span>
                      </li>
                    ))}
                  </ul>
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>
      </div>

      <div className="rounded-xl border border-border bg-card p-5">
        <h3 className="font-semibold mb-4">Regulatory change feed</h3>
        <div className="space-y-3">
          {alerts.map((a) => (
            <div
              key={a.id}
              className="rounded-lg border border-warning/30 bg-warning/5 p-4"
            >
              <div className="flex items-start gap-3">
                <AlertOctagon className="h-5 w-5 text-warning-foreground shrink-0" />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
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
          ))}
        </div>
      </div>
    </div>
  );
}

function Gauge({ value }: { value: number }) {
  const r = 56;
  const c = 2 * Math.PI * r;
  const offset = c - (value / 100) * c;
  return (
    <svg width="160" height="160" viewBox="0 0 140 140" className="mt-4">
      <circle
        cx="70"
        cy="70"
        r={r}
        stroke="var(--color-muted)"
        strokeWidth="12"
        fill="none"
      />
      <circle
        cx="70"
        cy="70"
        r={r}
        stroke="var(--color-success)"
        strokeWidth="12"
        fill="none"
        strokeDasharray={c}
        strokeDashoffset={offset}
        strokeLinecap="round"
        transform="rotate(-90 70 70)"
        style={{ transition: "stroke-dashoffset 600ms ease" }}
      />
      <text
        x="70"
        y="76"
        textAnchor="middle"
        fontSize="28"
        fontWeight="600"
        fill="var(--color-foreground)"
      >
        {value}%
      </text>
    </svg>
  );
}