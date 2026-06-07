import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import {
  Check,
  CircleDot,
  Loader2,
  Plus,
  Sparkles,
  Trash2,
  FileText,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  ShieldCheck,
  Download,
  Info,
  CheckCircle2,
  RefreshCw,
  Clock,
  Activity,
  Zap,
  Target,
  Thermometer,
  BarChart3,
  GripVertical,
} from "lucide-react";
import { api } from "@/lib/haccp/api";
import type { HACCPState, Stage } from "@/lib/haccp/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { FOOD_CATEGORIES } from "@/lib/haccp/categories";

export const Route = createFileRoute("/dashboard/plan-builder")({
  component: PlanBuilder,
});

// ── Stage definitions ──────────────────────────────────────────────────────

type StageDef = {
  id: Stage | "completed";
  label: string;
  desc: string;
  icon: React.ReactNode;
  isAuto?: boolean;
};

const STAGE_DEFS: StageDef[] = [
  { id: "intake",              label: "Business Setup",    desc: "Product & process definition",    icon: <Activity className="h-3.5 w-3.5" /> },
  { id: "hazard_analyzer",     label: "Hazard Analysis",   desc: "Review AI-identified hazards",    icon: <AlertTriangle className="h-3.5 w-3.5" /> },
  { id: "ccp_determinator",    label: "CCP Review",        desc: "Critical control points",         icon: <Target className="h-3.5 w-3.5" /> },
  { id: "limit_fetcher",       label: "Critical Limits",   desc: "FSSAI/Codex validated limits",    icon: <Thermometer className="h-3.5 w-3.5" /> },
  { id: "monitoring_designer", label: "Monitoring Design", desc: "Auto-generating procedures",      icon: <BarChart3 className="h-3.5 w-3.5" />, isAuto: true },
  { id: "corrective_action_gen", label: "Corrective Actions", desc: "Auto-generating actions",     icon: <Zap className="h-3.5 w-3.5" />, isAuto: true },
  { id: "completed",           label: "Plan Complete",     desc: "Certified & audit-ready",         icon: <ShieldCheck className="h-3.5 w-3.5" /> },
];

function stageIndex(state: HACCPState | null): number {
  if (!state) return -1;
  if (state.current_stage === "completed") return STAGE_DEFS.length - 1;
  return STAGE_DEFS.findIndex((s) => s.id === state.current_stage);
}

// ── Main Component ─────────────────────────────────────────────────────────

function PlanBuilder() {
  const [state, setState] = useState<HACCPState | null>(null);
  const [loading, setLoading] = useState(false);
  const [override, setOverride] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pastPlans, setPastPlans] = useState<any[]>([]);
  const [showHistory, setShowHistory] = useState(true);

  const idx = stageIndex(state);

  useEffect(() => {
    fetchPlans();
    const activeId = localStorage.getItem("active_haccp_plan_id");
    if (activeId) loadPlan(activeId);
  }, []);

  async function fetchPlans() {
    try {
      const list = await api.listPlans();
      setPastPlans(list);
    } catch (e) {
      console.error("Failed to fetch plans:", e);
    }
  }

  async function loadPlan(id: string) {
    setLoading(true);
    setError(null);
    try {
      const s = await api.getPlan(id);
      setState(s);
      setShowHistory(false);
      localStorage.setItem("active_haccp_plan_id", id);
    } catch (e) {
      setError((e as Error).message || "Failed to load plan.");
      localStorage.removeItem("active_haccp_plan_id");
    } finally {
      setLoading(false);
    }
  }

  async function start(input: { business_name: string; product_category: string; process_steps: string[] }) {
    setLoading(true);
    setError(null);
    try {
      const s = await api.startPlan(input);
      setState(s);
      setShowHistory(false);
      localStorage.setItem("active_haccp_plan_id", s.plan_id);
      fetchPlans();
    } catch (e) {
      setError((e as Error).message || "An error occurred starting the plan.");
    } finally {
      setLoading(false);
    }
  }

  async function resume(payload: Record<string, any>, gate: "hazard_review" | "ccp_review" | "limits_review") {
    if (!state) return;
    setLoading(true);
    setError(null);
    try {
      const s = await api.resume(state.plan_id, {
        gate,
        action: "approve",
        payload,
        justification: override || null,
      });
      setState(s);
      setOverride("");
      fetchPlans();
    } catch (e) {
      setError((e as Error).message || "An error occurred resuming the plan.");
    } finally {
      setLoading(false);
    }
  }

  function exitSession() {
    setState(null);
    setShowHistory(true);
    setError(null);
    localStorage.removeItem("active_haccp_plan_id");
    fetchPlans();
  }

  const isAutoStage =
    state &&
    (state.current_stage === "monitoring_designer" ||
      state.current_stage === "corrective_action_gen" ||
      state.current_stage === "verification_planner" ||
      state.current_stage === "record_generator" ||
      state.current_stage === "plan_validator" ||
      state.current_stage === "report_generator");

  return (
    <div className="grid lg:grid-cols-[240px_1fr] min-h-[calc(100vh-110px)] gap-0">
      {/* ── Stage Rail ── */}
      <aside className="border-r border-border bg-card/50 pr-0 flex flex-col">
        <div className="p-4 border-b border-border">
          <div className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground mb-1">HACCP Wizard</div>
          <div className="text-xs text-muted-foreground">
            {state ? (
              <span className="text-foreground font-medium truncate block">{state.business_name}</span>
            ) : (
              "No active plan"
            )}
          </div>
        </div>

        {/* Stage steps */}
        <nav className="p-3 space-y-0.5 flex-1">
          {STAGE_DEFS.map((s, i) => {
            const done = idx > i || state?.current_stage === "completed";
            const active = state?.current_stage === s.id || (s.id === "completed" && state?.current_stage === "completed");
            const pending = idx < i && state?.current_stage !== "completed";
            return (
              <div
                key={s.id}
                className={cn(
                  "flex items-center gap-2.5 rounded-lg px-3 py-2.5 transition-all duration-200",
                  done && "text-success",
                  active && "bg-primary/10 text-primary",
                  pending && "text-muted-foreground/50",
                  !pending && !active && !done && "text-muted-foreground",
                )}
              >
                {/* Status indicator */}
                <div className={cn(
                  "h-5 w-5 rounded-full flex items-center justify-center shrink-0 border text-[10px] font-bold transition-all",
                  done && "bg-success/15 border-success/40 text-success",
                  active && "bg-primary border-primary text-primary-foreground animate-pulse",
                  pending && "bg-transparent border-border/30",
                  !done && !active && !pending && "bg-muted border-border",
                )}>
                  {done ? <Check className="h-3 w-3" /> : active ? <CircleDot className="h-3 w-3" /> : <span className="opacity-40">{i + 1}</span>}
                </div>

                <div className="flex-1 min-w-0">
                  <div className={cn("text-xs font-semibold leading-tight", active && "text-primary", done && "text-success")}>
                    {s.label}
                  </div>
                  <div className="text-[10px] text-muted-foreground/70 leading-tight truncate mt-0.5">
                    {s.desc}
                  </div>
                </div>

                {s.isAuto && (
                  <span className="text-[9px] bg-muted text-muted-foreground px-1 py-0.5 rounded font-medium shrink-0">AUTO</span>
                )}
              </div>
            );
          })}
        </nav>

        {/* Plan history */}
        {!state && (
          <div className="border-t border-border">
            <button
              className="flex items-center justify-between w-full px-4 py-2.5 text-[11px] font-semibold text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
              onClick={() => setShowHistory((p) => !p)}
            >
              <span>Saved Plans ({pastPlans.length})</span>
              {showHistory ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
            </button>
            {showHistory && (
              <div className="px-3 pb-3 space-y-1 max-h-48 overflow-y-auto">
                {pastPlans.length === 0 ? (
                  <div className="text-[11px] text-muted-foreground text-center py-3 italic">No saved plans</div>
                ) : (
                  pastPlans.map((p) => {
                    const complete = p.status === "complete" || p.current_stage === "completed";
                    return (
                      <button
                        key={p.plan_id}
                        onClick={() => loadPlan(p.plan_id)}
                        disabled={loading}
                        className="w-full text-left px-2.5 py-1.5 rounded-md hover:bg-accent transition-colors text-[11px] group cursor-pointer"
                      >
                        <div className="font-medium text-foreground truncate">{p.business_name}</div>
                        <div className="flex items-center gap-1.5 mt-0.5">
                          <span className={cn(
                            "text-[9px] px-1.5 py-0.5 rounded-full font-semibold",
                            complete ? "bg-success/15 text-success" : "bg-amber-500/15 text-amber-600"
                          )}>
                            {complete ? "Done" : "Draft"}
                          </span>
                          <span className="text-muted-foreground truncate">{p.product_category}</span>
                        </div>
                      </button>
                    );
                  })
                )}
              </div>
            )}
          </div>
        )}

        {/* Exit active session */}
        {state && (
          <div className="p-3 border-t border-border">
            <Button
              variant="ghost"
              size="sm"
              className="w-full text-xs text-muted-foreground hover:text-destructive cursor-pointer"
              onClick={exitSession}
            >
              ← Exit to Plan History
            </Button>
          </div>
        )}
      </aside>

      {/* ── Main Content ── */}
      <div className="pl-6 pr-1 py-1 flex flex-col gap-5">
        {/* Error banner */}
        {error && (
          <div className="flex items-start gap-2.5 rounded-xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive animate-in fade-in">
            <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
            <div className="flex-1">{error}</div>
            <button onClick={() => setError(null)} className="text-destructive/60 hover:text-destructive cursor-pointer text-xs">✕</button>
          </div>
        )}

        {/* Stage content */}
        {!state ? (
          /* No active plan — show intake form */
          <IntakeForm onStart={start} loading={loading} />
        ) : loading && isAutoStage ? (
          <AutoProcessingPanel stage={state.current_stage} />
        ) : state.current_stage === "hazard_analyzer" ? (
          <HazardReviewPanel
            state={state}
            onApprove={(hazards) => resume({ hazards }, "hazard_review")}
            loading={loading}
          />
        ) : state.current_stage === "ccp_determinator" ? (
          <CcpReviewPanel
            state={state}
            override={override}
            setOverride={setOverride}
            onApprove={(ccps) => resume({ ccps }, "ccp_review")}
            loading={loading}
          />
        ) : state.current_stage === "limit_fetcher" ? (
          <LimitsReviewPanel
            state={state}
            onApprove={(critical_limits) => resume({ critical_limits }, "limits_review")}
            loading={loading}
          />
        ) : state.current_stage === "completed" ? (
          <CompletedPanel state={state} onReset={exitSession} />
        ) : (
          <AutoProcessingPanel stage={state.current_stage} />
        )}
      </div>
    </div>
  );
}

// ── Intake Form ────────────────────────────────────────────────────────────

function IntakeForm({
  onStart,
  loading,
}: {
  onStart: (input: { business_name: string; product_category: string; process_steps: string[] }) => void;
  loading: boolean;
}) {
  const [business, setBusiness] = useState("Demo FBO Pvt. Ltd.");
  const [category, setCategory] = useState<string>("Dairy Pasteurized");
  const [steps, setSteps] = useState<string[]>([
    "Raw Milk Reception",
    "Pre-heat Treatment Storage",
    "Pasteurization (72°C / 15s)",
    "Cooling to ≤5°C",
    "Filling & Packaging",
    "Cold Chain Dispatch",
  ]);
  const [newStep, setNewStep] = useState("");
  const [dragIdx, setDragIdx] = useState<number | null>(null);

  function addStep() {
    if (newStep.trim()) {
      setSteps((p) => [...p, newStep.trim()]);
      setNewStep("");
    }
  }

  function removeStep(i: number) {
    setSteps((p) => p.filter((_, idx) => idx !== i));
  }

  function handleDragStart(i: number) { setDragIdx(i); }
  function handleDragOver(e: React.DragEvent, i: number) {
    e.preventDefault();
    if (dragIdx === null || dragIdx === i) return;
    setSteps((p) => {
      const arr = [...p];
      const [item] = arr.splice(dragIdx, 1);
      arr.splice(i, 0, item);
      return arr;
    });
    setDragIdx(i);
  }

  return (
    <div className="max-w-2xl space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-2 text-xs font-semibold text-primary bg-primary/10 border border-primary/20 px-3 py-1 rounded-full mb-3">
          <Sparkles className="h-3 w-3" /> AI-Powered HACCP Generation
        </div>
        <h2 className="text-xl font-bold tracking-tight">Start a New HACCP Plan</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Define your food business and process flow. Our AI will analyze hazards and generate a complete, FSSAI-compliant HACCP plan.
        </p>
      </div>

      {/* Business details card */}
      <div className="rounded-xl border border-border bg-card p-5 space-y-4">
        <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Business Details</div>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <label className="text-xs font-medium">Business / FBO Name</label>
            <Input
              value={business}
              onChange={(e) => setBusiness(e.target.value)}
              placeholder="e.g. Sunrise Dairy Pvt. Ltd."
              className="text-sm"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium">Product Category</label>
            <Select value={category} onValueChange={setCategory}>
              <SelectTrigger className="w-full bg-background text-sm">
                <SelectValue placeholder="Select category" />
              </SelectTrigger>
              <SelectContent>
                {FOOD_CATEGORIES.map((cat) => (
                  <SelectItem key={cat.label} value={cat.label}>
                    {cat.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      {/* Process steps card */}
      <div className="rounded-xl border border-border bg-card p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Process Flow</div>
            <div className="text-[11px] text-muted-foreground mt-0.5">Drag steps to reorder. Add all steps in production order.</div>
          </div>
          <div className="text-[10px] bg-muted text-muted-foreground px-2 py-0.5 rounded-full">{steps.length} steps</div>
        </div>

        <div className="space-y-1.5">
          {steps.map((step, i) => (
            <div
              key={i}
              draggable
              onDragStart={() => handleDragStart(i)}
              onDragOver={(e) => handleDragOver(e, i)}
              onDragEnd={() => setDragIdx(null)}
              className={cn(
                "flex items-center gap-2.5 rounded-lg border border-border bg-background px-3 py-2.5 text-sm cursor-grab transition-all duration-150",
                dragIdx === i && "opacity-50 border-primary/50 shadow-sm"
              )}
            >
              <GripVertical className="h-3.5 w-3.5 text-muted-foreground/50 shrink-0" />
              <span className="text-[10px] font-bold text-muted-foreground w-5 shrink-0">{i + 1}</span>
              <span className="flex-1 text-sm">{step}</span>
              <button
                onClick={() => removeStep(i)}
                className="text-muted-foreground/40 hover:text-destructive transition-colors cursor-pointer p-0.5"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}
        </div>

        <div className="flex gap-2">
          <Input
            value={newStep}
            onChange={(e) => setNewStep(e.target.value)}
            placeholder="Add step (e.g. Metal Detection)"
            className="text-sm"
            onKeyDown={(e) => { if (e.key === "Enter") addStep(); }}
          />
          <Button variant="outline" onClick={addStep} className="cursor-pointer shrink-0">
            <Plus className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Submit */}
      <Button
        size="lg"
        className="w-full cursor-pointer font-semibold gap-2"
        disabled={loading || steps.length < 2 || !business.trim()}
        onClick={() => onStart({ business_name: business, product_category: category, process_steps: steps })}
      >
        {loading ? (
          <><Loader2 className="h-4 w-4 animate-spin" /> Analyzing Hazards...</>
        ) : (
          <><Sparkles className="h-4 w-4" /> Generate HACCP Hazard Analysis</>
        )}
      </Button>

      {steps.length < 2 && (
        <p className="text-xs text-muted-foreground text-center">Add at least 2 process steps to begin analysis.</p>
      )}
    </div>
  );
}

// ── Hazard Review Panel ────────────────────────────────────────────────────

function HazardReviewPanel({
  state,
  onApprove,
  loading,
}: {
  state: HACCPState;
  onApprove: (h: HACCPState["hazards_identified"]) => void;
  loading: boolean;
}) {
  const [hazards, setHazards] = useState(
    (state.hazards_identified || []).map((h) => ({ ...h, user_confirmed: true }))
  );

  const confirmed = hazards.filter((h) => h.user_confirmed).length;

  function rpnColor(rpn: number) {
    if (rpn >= 15) return "text-destructive bg-destructive/10 border-destructive/30";
    if (rpn >= 9)  return "text-warning-foreground bg-warning/10 border-warning/30";
    return "text-success bg-success/10 border-success/30";
  }

  function categoryIcon(cat: string) {
    if (cat === "biological") return "🦠";
    if (cat === "chemical")   return "⚗️";
    return "🔩";
  }

  return (
    <div className="space-y-5 animate-in fade-in duration-300">
      {/* Panel header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <AlertTriangle className="h-4 w-4 text-warning-foreground" />
            <span className="text-[11px] font-semibold text-warning-foreground uppercase tracking-wider">Step 2 of 7 — Hazard Analysis</span>
          </div>
          <h2 className="text-xl font-bold">Review Identified Hazards</h2>
          <p className="text-sm text-muted-foreground mt-1">
            AI analyzed your process and identified <strong>{hazards.length} hazards</strong> across{" "}
            <strong>{new Set(hazards.map((h) => h.process_step)).size} process steps</strong>. Uncheck any to exclude from the plan.
          </p>
        </div>
        <div className="text-right shrink-0">
          <div className="text-2xl font-bold text-primary">{confirmed}</div>
          <div className="text-[11px] text-muted-foreground">confirmed</div>
        </div>
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-3 gap-3">
        {(["biological", "chemical", "physical"] as const).map((cat) => {
          const count = hazards.filter((h) => h.category === cat).length;
          return (
            <div key={cat} className="rounded-lg border border-border bg-card p-3 text-center">
              <div className="text-xl">{categoryIcon(cat)}</div>
              <div className="text-lg font-bold mt-1">{count}</div>
              <div className="text-[10px] text-muted-foreground capitalize">{cat}</div>
            </div>
          );
        })}
      </div>

      {/* Hazard cards */}
      <div className="space-y-2.5 max-h-[460px] overflow-y-auto pr-1">
        {hazards.map((h, i) => (
          <div
            key={i}
            className={cn(
              "rounded-xl border p-4 transition-all duration-200",
              h.user_confirmed ? "border-border bg-card" : "border-border/50 bg-muted/20 opacity-60"
            )}
          >
            <div className="flex items-start gap-3">
              {/* Toggle */}
              <input
                type="checkbox"
                checked={h.user_confirmed}
                onChange={(e) =>
                  setHazards((prev) =>
                    prev.map((x, idx) => idx === i ? { ...x, user_confirmed: e.target.checked } : x)
                  )
                }
                className="mt-1 h-4 w-4 rounded border-border accent-primary cursor-pointer"
              />

              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="font-semibold text-sm leading-tight">{h.name}</div>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[10px] bg-muted px-2 py-0.5 rounded-full text-muted-foreground font-medium">
                        {categoryIcon(h.category)} {h.category}
                      </span>
                      <span className="text-[10px] text-muted-foreground">→ {h.process_step}</span>
                    </div>
                  </div>
                  <span className={cn("text-[11px] font-bold px-2.5 py-1 rounded-full border shrink-0", rpnColor(h.rpn))}>
                    RPN {h.rpn}
                  </span>
                </div>

                <div className="mt-2.5 text-[11px] text-muted-foreground leading-relaxed bg-muted/30 rounded-lg px-3 py-2">
                  <span className="font-medium">Control: </span>{h.recommended_control}
                </div>

                {h.citations?.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {h.citations.map((c: string) => (
                      <span key={c} className="text-[9px] bg-primary/5 text-primary border border-primary/15 px-2 py-0.5 rounded-full">
                        {c}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Action */}
      <div className="border-t border-border pt-4">
        <Button
          className="w-full cursor-pointer font-semibold gap-2"
          size="lg"
          disabled={loading || confirmed === 0}
          onClick={() => onApprove(hazards.filter((h) => h.user_confirmed))}
        >
          {loading ? (
            <><Loader2 className="h-4 w-4 animate-spin" /> Running Codex Decision Tree...</>
          ) : (
            <><Check className="h-4 w-4" /> Confirm {confirmed} Hazard{confirmed !== 1 ? "s" : ""} & Determine CCPs</>
          )}
        </Button>
      </div>
    </div>
  );
}

// ── CCP Review Panel ───────────────────────────────────────────────────────

function CcpReviewPanel({
  state,
  override,
  setOverride,
  onApprove,
  loading,
}: {
  state: HACCPState;
  override: string;
  setOverride: (v: string) => void;
  onApprove: (ccps: any[]) => void;
  loading: boolean;
}) {
  // Initialize from candidates (all that are already CCP)
  const [selected, setSelected] = useState<Set<number>>(() => {
    const s = new Set<number>();
    (state.ccp_candidates || []).forEach((c, i) => {
      if (c.is_ccp) s.add(i);
    });
    return s;
  });
  const [openIdx, setOpenIdx] = useState<number | null>(null);

  const candidates = state.ccp_candidates || [];
  const selectedCcps = candidates
    .filter((_, i) => selected.has(i))
    .map((c) => ({
      hazard_name: c.hazard_name,
      process_step: c.process_step,
      decision_tree_path: c.decision_tree_path || [],
      user_override: !c.is_ccp, // if the user re-enabled a non-CCP, it's an override
      override_justification: !c.is_ccp ? override || "User-defined CCP" : null,
    }));

  return (
    <div className="space-y-5 animate-in fade-in duration-300">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Target className="h-4 w-4 text-primary" />
            <span className="text-[11px] font-semibold text-primary uppercase tracking-wider">Step 3 of 7 — CCP Determination</span>
          </div>
          <h2 className="text-xl font-bold">Critical Control Points</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Codex 2020 decision tree evaluated <strong>{candidates.length} hazards</strong>. Toggle any hazard to override the AI recommendation.
          </p>
        </div>
        <div className="text-right shrink-0">
          <div className="text-2xl font-bold text-primary">{selected.size}</div>
          <div className="text-[11px] text-muted-foreground">CCPs selected</div>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 text-[11px]">
        <div className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full bg-primary"></span><span>CCP — Requires critical control</span></div>
        <div className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full bg-muted-foreground/30"></span><span>PRP — Controlled by GMP/SOP</span></div>
      </div>

      {/* Candidate cards */}
      <div className="space-y-2.5 max-h-[420px] overflow-y-auto pr-1">
        {candidates.map((c, i) => {
          const isSel = selected.has(i);
          const isExpanded = openIdx === i;
          return (
            <div
              key={i}
              className={cn(
                "rounded-xl border transition-all duration-200",
                isSel ? "border-primary/40 bg-primary/5" : "border-border bg-card"
              )}
            >
              <div className="flex items-center gap-3 px-4 py-3">
                {/* Toggle */}
                <button
                  onClick={() =>
                    setSelected((prev) => {
                      const next = new Set(prev);
                      if (next.has(i)) next.delete(i); else next.add(i);
                      return next;
                    })
                  }
                  className={cn(
                    "h-6 w-6 rounded-full border-2 flex items-center justify-center transition-all cursor-pointer shrink-0",
                    isSel ? "bg-primary border-primary text-white" : "border-border bg-transparent"
                  )}
                >
                  {isSel && <Check className="h-3 w-3" />}
                </button>

                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-sm">{c.hazard_name}</div>
                  <div className="text-[11px] text-muted-foreground">{c.process_step}</div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  {/* CCP badge */}
                  <span className={cn(
                    "text-[10px] font-bold px-2.5 py-1 rounded-full border",
                    isSel ? "bg-primary text-primary-foreground border-primary" : "bg-muted text-muted-foreground border-border"
                  )}>
                    {isSel ? "CCP" : "PRP"}
                  </span>
                  {!c.is_ccp && isSel && (
                    <span className="text-[9px] bg-warning/10 text-warning-foreground border border-warning/30 px-2 py-0.5 rounded-full">Override</span>
                  )}

                  {/* Expand button */}
                  <button
                    onClick={() => setOpenIdx(isExpanded ? null : i)}
                    className="text-muted-foreground hover:text-foreground cursor-pointer p-1 transition-colors"
                  >
                    {isExpanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                  </button>
                </div>
              </div>

              {/* Expanded decision tree */}
              {isExpanded && (
                <div className="px-4 pb-4 border-t border-border/50 mt-0 pt-3 space-y-2">
                  <div className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Codex Decision Tree Path</div>
                  <ol className="space-y-1">
                    {(c.decision_tree_path || []).map((step: string, si: number) => (
                      <li key={si} className="flex items-start gap-2 text-[11px] text-muted-foreground">
                        <span className="text-primary font-bold shrink-0">Q{si + 1}</span>
                        <span>{step.replace(/^Q\d+:\s*/, "")}</span>
                      </li>
                    ))}
                  </ol>
                  {c.reasoning && (
                    <div className="mt-2 text-[11px] text-muted-foreground italic bg-muted/40 rounded-lg px-3 py-2 leading-relaxed">
                      <Info className="inline h-3 w-3 mr-1 -mt-0.5" />
                      {c.reasoning}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Override justification */}
      {[...selected].some((i) => !(candidates[i]?.is_ccp)) && (
        <div className="rounded-lg border border-warning/30 bg-warning/5 p-3 space-y-2">
          <div className="text-[11px] font-semibold text-warning-foreground flex items-center gap-1.5">
            <AlertTriangle className="h-3.5 w-3.5" /> Override justification required
          </div>
          <Textarea
            placeholder="Explain why these steps require CCP control beyond the AI recommendation..."
            value={override}
            onChange={(e) => setOverride(e.target.value)}
            className="text-xs min-h-[60px]"
          />
        </div>
      )}

      {/* Action */}
      <div className="border-t border-border pt-4">
        <Button
          className="w-full cursor-pointer font-semibold gap-2"
          size="lg"
          disabled={loading}
          onClick={() => onApprove(selectedCcps)}
        >
          {loading ? (
            <><Loader2 className="h-4 w-4 animate-spin" /> Fetching Critical Limits...</>
          ) : (
            <><ShieldCheck className="h-4 w-4" /> Approve {selected.size} CCP{selected.size !== 1 ? "s" : ""} & Fetch Critical Limits</>
          )}
        </Button>
        <p className="text-[11px] text-muted-foreground text-center mt-2">
          Critical limits will be retrieved directly from FSSAI Schedule 4 and Codex CAC/RCP standards.
        </p>
      </div>
    </div>
  );
}

// ── Limits Review Panel ────────────────────────────────────────────────────

function LimitsReviewPanel({
  state,
  onApprove,
  loading,
}: {
  state: HACCPState;
  onApprove: (limits: HACCPState["critical_limits"]) => void;
  loading: boolean;
}) {
  const [limits, setLimits] = useState<HACCPState["critical_limits"]>(state.critical_limits || {});
  const [validated, setValidated] = useState<Set<string>>(new Set());

  const entries = Object.entries(limits);
  const allValidated = entries.length > 0 && entries.every(([k]) => validated.has(k));

  function updateLimit(key: string, field: string, value: any) {
    setLimits((prev) => ({ ...prev, [key]: { ...prev[key], [field]: value } }));
  }

  function toggleValidate(key: string) {
    setLimits((prev) => ({ ...prev, [key]: { ...prev[key], user_validated: !prev[key]?.user_validated } }));
    setValidated((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key); else next.add(key);
      return next;
    });
  }

  return (
    <div className="space-y-5 animate-in fade-in duration-300">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Thermometer className="h-4 w-4 text-blue-500" />
            <span className="text-[11px] font-semibold text-blue-500 uppercase tracking-wider">Step 4 of 7 — Critical Limits</span>
          </div>
          <h2 className="text-xl font-bold">Validate Critical Limits</h2>
          <p className="text-sm text-muted-foreground mt-1">
            These limits are grounded in FSSAI & Codex regulatory documents. Adjust with caution — validate each before proceeding.
          </p>
        </div>
        <div className="text-right shrink-0">
          <div className="text-2xl font-bold text-blue-500">{validated.size}/{entries.length}</div>
          <div className="text-[11px] text-muted-foreground">validated</div>
        </div>
      </div>

      {entries.length === 0 ? (
        <div className="flex flex-col items-center justify-center text-center p-12 rounded-xl border border-destructive/30 bg-destructive/5">
          <AlertTriangle className="h-8 w-8 text-destructive mb-3" />
          <div className="font-semibold text-destructive">No critical limits found</div>
          <div className="text-sm text-muted-foreground mt-1">The limit fetcher ran but returned no data. Go back and re-approve CCPs.</div>
        </div>
      ) : (
        <div className="space-y-3 max-h-[460px] overflow-y-auto pr-1">
          {entries.map(([hazard, lim]) => {
            const isVal = validated.has(hazard);
            return (
              <div
                key={hazard}
                className={cn(
                  "rounded-xl border p-4 transition-all duration-200",
                  isVal ? "border-success/40 bg-success/5" : "border-border bg-card"
                )}
              >
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div>
                    <div className="font-semibold text-sm leading-snug">{hazard}</div>
                    <div className="text-[11px] text-muted-foreground mt-0.5">{lim.parameter}</div>
                  </div>
                  <button
                    onClick={() => toggleValidate(hazard)}
                    className={cn(
                      "flex items-center gap-1.5 text-[11px] font-semibold px-3 py-1.5 rounded-full border transition-all cursor-pointer shrink-0",
                      isVal
                        ? "bg-success/15 border-success/40 text-success"
                        : "bg-transparent border-border text-muted-foreground hover:border-success/40 hover:text-success"
                    )}
                  >
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    {isVal ? "Validated" : "Validate"}
                  </button>
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <div className="space-y-1">
                    <label className="text-[10px] text-muted-foreground font-medium uppercase tracking-wide">Min Value</label>
                    <Input
                      type="number"
                      value={lim.min_value ?? ""}
                      onChange={(e) => updateLimit(hazard, "min_value", e.target.value === "" ? null : Number(e.target.value))}
                      className="text-sm h-8"
                      placeholder="—"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] text-muted-foreground font-medium uppercase tracking-wide">Max Value</label>
                    <Input
                      type="number"
                      value={lim.max_value ?? ""}
                      onChange={(e) => updateLimit(hazard, "max_value", e.target.value === "" ? null : Number(e.target.value))}
                      className="text-sm h-8"
                      placeholder="—"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] text-muted-foreground font-medium uppercase tracking-wide">Unit</label>
                    <Input
                      value={lim.unit}
                      onChange={(e) => updateLimit(hazard, "unit", e.target.value)}
                      className="text-sm h-8"
                      placeholder="°C"
                    />
                  </div>
                </div>

                {lim.source_citation && (
                  <div className="mt-3 flex items-start gap-1.5">
                    <FileText className="h-3 w-3 text-muted-foreground shrink-0 mt-0.5" />
                    <span className="text-[10px] text-muted-foreground">{lim.source_citation}</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      <div className="border-t border-border pt-4">
        <Button
          className="w-full cursor-pointer font-semibold gap-2"
          size="lg"
          disabled={loading || entries.length === 0}
          onClick={() => {
            // Mark all as validated before submitting
            const finalLimits = Object.fromEntries(
              entries.map(([k, v]) => [k, { ...v, user_validated: true }])
            );
            onApprove(finalLimits);
          }}
        >
          {loading ? (
            <><Loader2 className="h-4 w-4 animate-spin" /> Designing Monitoring Procedures...</>
          ) : (
            <><Check className="h-4 w-4" /> Validate Limits & Design Monitoring Plan</>
          )}
        </Button>
        {!allValidated && entries.length > 0 && (
          <p className="text-[11px] text-muted-foreground text-center mt-2">
            You can proceed without validating each limit individually — all will be marked as validated.
          </p>
        )}
      </div>
    </div>
  );
}

// ── Auto Processing Panel ──────────────────────────────────────────────────

const PROCESSING_STEPS_MAP: Record<string, { label: string; steps: string[] }> = {
  monitoring_designer: {
    label: "Designing Monitoring Procedures",
    steps: [
      "Assigning monitoring methods per CCP...",
      "Calibrating frequencies with FSSAI guidelines...",
      "Generating record formats...",
      "Assigning responsible persons...",
      "Finalizing monitoring schedule...",
    ],
  },
  corrective_action_gen: {
    label: "Generating Corrective Actions",
    steps: [
      "Identifying deviation triggers per CCP...",
      "Drafting immediate response procedures...",
      "Generating root-cause investigation steps...",
      "Assigning personnel responsibilities...",
      "Linking to verification checklist...",
    ],
  },
  default: {
    label: "Processing Plan",
    steps: [
      "Running HACCP nodes...",
      "Applying regulatory constraints...",
      "Generating documentation...",
      "Finalizing plan records...",
      "Completing verification...",
    ],
  },
};

function AutoProcessingPanel({ stage }: { stage: string }) {
  const [step, setStep] = useState(0);
  const info = PROCESSING_STEPS_MAP[stage] ?? PROCESSING_STEPS_MAP.default;

  useEffect(() => {
    const timers = [1500, 3000, 5000, 7000, 9000].map((ms, idx) =>
      setTimeout(() => setStep(idx + 1), ms)
    );
    return () => timers.forEach(clearTimeout);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center min-h-[500px] text-center space-y-6 animate-in fade-in duration-300">
      <div className="relative">
        <div className="h-20 w-20 rounded-full bg-primary/10 flex items-center justify-center">
          <Loader2 className="h-10 w-10 text-primary animate-spin" />
        </div>
        <div className="absolute -top-1 -right-1 h-5 w-5 rounded-full bg-success flex items-center justify-center">
          <Sparkles className="h-3 w-3 text-white" />
        </div>
      </div>

      <div className="space-y-1">
        <h3 className="text-lg font-bold">{info.label}</h3>
        <p className="text-sm text-muted-foreground animate-pulse">
          {info.steps[Math.min(step, info.steps.length - 1)]}
        </p>
      </div>

      <div className="w-72 space-y-2">
        <div className="flex justify-between text-[11px] text-muted-foreground">
          <span>Progress</span>
          <span>{Math.round(((step + 1) / info.steps.length) * 100)}%</span>
        </div>
        <div className="h-2 bg-muted rounded-full overflow-hidden">
          <div
            className="h-full bg-primary rounded-full transition-all duration-700"
            style={{ width: `${((step + 1) / info.steps.length) * 100}%` }}
          />
        </div>
      </div>

      <div className="text-[11px] text-muted-foreground flex items-center gap-1.5">
        <Clock className="h-3 w-3" /> This usually takes 15–30 seconds
      </div>
    </div>
  );
}

// ── Completed Panel ────────────────────────────────────────────────────────

function CompletedPanel({
  state,
  onReset,
}: {
  state: HACCPState;
  onReset: () => void;
}) {
  const [downloading, setDownloading] = useState(false);

  async function downloadPdf() {
    setDownloading(true);
    try {
      await api.generatePdf(state.plan_id);
      window.open(api.pdfUrl(state.plan_id), "_blank");
    } catch (e) {
      alert("PDF generation failed: " + (e as Error).message);
    } finally {
      setDownloading(false);
    }
  }

  const stats = [
    { label: "Hazards Identified", value: state.hazards_identified?.length || 0, icon: <AlertTriangle className="h-4 w-4" />, color: "text-warning-foreground" },
    { label: "CCPs Approved",      value: state.ccps_approved?.length || 0,      icon: <Target className="h-4 w-4" />,         color: "text-primary" },
    { label: "Monitoring Procs.",  value: state.monitoring_procedures?.length || 0, icon: <BarChart3 className="h-4 w-4" />,  color: "text-blue-500" },
    { label: "Corrective Actions", value: state.corrective_actions?.length || 0, icon: <Zap className="h-4 w-4" />,            color: "text-purple-500" },
  ];

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Hero */}
      <div className="rounded-2xl border border-success/30 bg-gradient-to-br from-success/10 to-emerald-500/5 p-8 text-center relative overflow-hidden">
        <div className="absolute inset-0 opacity-5">
          <ShieldCheck className="h-full w-full" />
        </div>
        <div className="relative">
          <div className="inline-flex h-16 w-16 items-center justify-center rounded-full bg-success/20 border border-success/40 mb-4">
            <CheckCircle2 className="h-8 w-8 text-success" />
          </div>
          <h2 className="text-2xl font-bold">HACCP Plan Complete</h2>
          <p className="text-sm text-muted-foreground mt-2 max-w-md mx-auto">
            Your HACCP plan for <strong>{state.business_name}</strong> ({state.product_category}) is fully generated, FSSAI-compliant, and audit-ready.
          </p>
          <div className="mt-4 inline-flex items-center gap-2 text-xs bg-background/80 border border-success/30 px-4 py-2 rounded-full text-success font-medium">
            <ShieldCheck className="h-3.5 w-3.5" /> Grounded in FSSAI Schedule 4 & Codex CAC/RCP
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {stats.map((s) => (
          <div key={s.label} className="rounded-xl border border-border bg-card p-4 text-center">
            <div className={cn("flex justify-center mb-2", s.color)}>{s.icon}</div>
            <div className="text-2xl font-bold">{s.value}</div>
            <div className="text-[11px] text-muted-foreground mt-0.5">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Records generated */}
      {(state.records_generated?.length || 0) > 0 && (
        <div className="rounded-xl border border-border bg-card p-4">
          <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">Generated Records</div>
          <div className="grid grid-cols-2 gap-2">
            {(state.records_generated || []).map((r) => (
              <div key={r} className="flex items-center gap-2 text-sm text-muted-foreground">
                <FileText className="h-3.5 w-3.5 text-primary shrink-0" />
                {r}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="grid grid-cols-2 gap-3">
        <Button
          size="lg"
          className="cursor-pointer font-semibold gap-2"
          onClick={downloadPdf}
          disabled={downloading}
        >
          {downloading ? (
            <><Loader2 className="h-4 w-4 animate-spin" /> Generating...</>
          ) : (
            <><Download className="h-4 w-4" /> Download PDF Report</>
          )}
        </Button>
        <Button
          size="lg"
          variant="outline"
          className="cursor-pointer font-semibold gap-2"
          onClick={onReset}
        >
          <RefreshCw className="h-4 w-4" /> Start New Plan
        </Button>
      </div>

      <div className="rounded-lg bg-muted/40 border border-border p-3 text-[11px] text-muted-foreground text-center">
        Plan ID: <code className="font-mono bg-muted px-1.5 py-0.5 rounded">{state.plan_id}</code>
        &nbsp;·&nbsp;Navigate to <strong>CCP Monitor</strong> to start logging real-time temperature readings.
      </div>
    </div>
  );
}