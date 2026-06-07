import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  Download,
  FileText,
  Loader2,
  Code,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import { api } from "@/lib/haccp/api";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/dashboard/reports")({
  component: ReportsPage,
});

const STAGE_STEPS = [
  "intake_processor",
  "hazard_analyzer",
  "ccp_determinator",
  "critical_limit_fetcher",
  "monitoring_designer",
  "corrective_action_gen",
  "verification_planner",
  "record_generator",
  "plan_validator",
  "report_generator",
  "completed",
];

const STAGE_LABELS: Record<string, string> = {
  intake_processor: "Intake",
  hazard_analyzer: "Hazards",
  ccp_determinator: "CCPs",
  critical_limit_fetcher: "Limits",
  monitoring_designer: "Monitoring",
  corrective_action_gen: "Corrective",
  verification_planner: "Verification",
  record_generator: "Records",
  plan_validator: "Validation",
  report_generator: "Report",
  completed: "Done",
};

function PlanProgressBar({ currentStage }: { currentStage: string }) {
  const currentIdx = STAGE_STEPS.indexOf(currentStage);
  const pct = Math.round(((currentIdx + 1) / STAGE_STEPS.length) * 100);

  return (
    <div className="mt-3 space-y-1.5">
      <div className="flex items-center justify-between text-[11px] text-muted-foreground">
        <span>Plan completion</span>
        <span className="font-medium">{pct}%</span>
      </div>
      <div className="h-1.5 rounded-full bg-muted overflow-hidden">
        <div
          className="h-full rounded-full bg-primary transition-all duration-700"
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="text-[10px] text-muted-foreground">
        Stage: <span className="font-medium">{STAGE_LABELS[currentStage] ?? currentStage}</span>
      </div>
    </div>
  );
}

function ReportsPage() {
  const [plans, setPlans] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [ready, setReady] = useState<Record<string, boolean>>({});
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  async function loadPlans() {
    setLoading(true);
    try {
      const list = await api.listPlans();
      setPlans(list);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadPlans();
  }, []);

  async function generate(id: string) {
    setBusy(id);
    try {
      await api.generatePdf(id);
      setReady((r) => ({ ...r, [id]: true }));
    } catch (e) {
      alert("Failed to generate PDF: " + (e as Error).message);
    } finally {
      setBusy(null);
    }
  }

  function toggleJsonPreview(id: string) {
    setExpanded((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  const completedPlans = plans.filter(
    (p) => p.current_stage === "completed" || p.current_stage === "report_generator",
  );
  const inProgressPlans = plans.filter(
    (p) => p.current_stage !== "completed" && p.current_stage !== "report_generator",
  );

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-primary to-teal-500 bg-clip-text text-transparent">
          Report Generation
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Audit-ready PDFs and JSON exports for every HACCP plan — formatted for FSSAI inspection submission.
        </p>
      </div>

      {loading && plans.length === 0 ? (
        <div className="flex items-center justify-center p-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : plans.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border bg-card p-10 text-center text-sm text-muted-foreground">
          No plans yet. Build one in the <strong>Plan Builder</strong> first.
        </div>
      ) : null}

      {/* Completed Plans */}
      {completedPlans.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <CheckCircle2 className="h-4 w-4 text-success" />
            Ready for Report Generation
            <span className="ml-1 text-xs text-muted-foreground font-normal">({completedPlans.length})</span>
          </div>
          <div className="space-y-3">
            {completedPlans.map((p) => (
              <div
                key={p.plan_id}
                className="rounded-xl border border-border bg-card overflow-hidden transition-all hover:border-primary/20"
              >
                <div className="p-5 flex items-center gap-4">
                  <div className="h-10 w-10 rounded-md bg-primary/10 text-primary flex items-center justify-center shrink-0">
                    <FileText className="h-5 w-5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate">
                      {p.business_name} · {p.product_category}
                    </div>
                    <div className="text-xs text-muted-foreground mt-0.5">
                      {p.ccps_approved?.length ?? 0} CCPs · Plan ID:{" "}
                      <code className="text-[10px]">{p.plan_id.slice(0, 8)}…</code>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => toggleJsonPreview(p.plan_id)}
                      className="gap-1 text-muted-foreground hover:text-foreground cursor-pointer"
                      id={`json-preview-${p.plan_id}`}
                    >
                      <Code className="h-3.5 w-3.5" />
                      JSON
                      {expanded[p.plan_id] ? (
                        <ChevronUp className="h-3.5 w-3.5" />
                      ) : (
                        <ChevronDown className="h-3.5 w-3.5" />
                      )}
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        const blob = new Blob([JSON.stringify(p, null, 2)], {
                          type: "application/json",
                        });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement("a");
                        a.href = url;
                        a.download = `${p.plan_id}.json`;
                        a.click();
                        URL.revokeObjectURL(url);
                      }}
                      className="cursor-pointer"
                    >
                      <Download className="h-3.5 w-3.5" />
                    </Button>
                    {ready[p.plan_id] ? (
                      <a href={api.pdfUrl(p.plan_id)} target="_blank" rel="noreferrer">
                        <Button size="sm" id={`download-pdf-${p.plan_id}`}>
                          <Download className="h-4 w-4 mr-1" /> Download PDF
                        </Button>
                      </a>
                    ) : (
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={busy === p.plan_id}
                        onClick={() => generate(p.plan_id)}
                        id={`generate-pdf-${p.plan_id}`}
                        className="cursor-pointer"
                      >
                        {busy === p.plan_id ? (
                          <Loader2 className="h-4 w-4 animate-spin mr-1" />
                        ) : null}
                        Generate PDF
                      </Button>
                    )}
                  </div>
                </div>

                {/* JSON Preview Panel */}
                {expanded[p.plan_id] && (
                  <div className="border-t border-border bg-muted/30 p-4 animate-in slide-in-from-top-2 duration-200">
                    <div className="text-xs font-medium text-muted-foreground mb-2">
                      Structured plan data (preview)
                    </div>
                    <pre className="text-[11px] text-foreground overflow-auto max-h-60 leading-relaxed">
                      {JSON.stringify(
                        {
                          plan_id: p.plan_id,
                          business_name: p.business_name,
                          product_category: p.product_category,
                          current_stage: p.current_stage,
                          status: p.status,
                          ccps_approved: p.ccps_approved,
                        },
                        null,
                        2,
                      )}
                    </pre>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* In-Progress Plans */}
      {inProgressPlans.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <AlertCircle className="h-4 w-4 text-warning-foreground" />
            In Progress — Complete to Enable PDF
            <span className="ml-1 text-xs text-muted-foreground font-normal">({inProgressPlans.length})</span>
          </div>
          <div className="space-y-3">
            {inProgressPlans.map((p) => (
              <div
                key={p.plan_id}
                className="rounded-xl border border-border bg-card p-5 opacity-80"
              >
                <div className="flex items-center gap-4">
                  <div className="h-10 w-10 rounded-md bg-muted text-muted-foreground flex items-center justify-center shrink-0">
                    <FileText className="h-5 w-5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate">
                      {p.business_name} · {p.product_category}
                    </div>
                    <PlanProgressBar currentStage={p.current_stage} />
                  </div>
                  <span className="text-[11px] px-2 py-0.5 rounded-full border border-border bg-muted text-muted-foreground shrink-0">
                    in progress
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}