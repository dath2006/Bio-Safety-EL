import type {
  ChatResponse,
  ComplianceAlert,
  HACCPState,
  HumanDecision,
  MonitoringLog,
  Stage,
} from "./types";

const plans = new Map<string, HACCPState>();
const logs = new Map<string, MonitoringLog[]>();

function uid() {
  return "plan_" + Math.random().toString(36).slice(2, 10);
}

function baseState(
  plan_id: string,
  business_name: string,
  product_category: string,
  process_steps: string[],
): HACCPState {
  return {
    plan_id,
    user_id: "demo-user",
    business_name,
    product_category,
    process_steps,
    hazards_identified: [],
    hazards_user_confirmed: false,
    ccp_candidates: [],
    ccps_approved: [],
    ccps_user_approved: false,
    critical_limits: {},
    monitoring_procedures: [],
    corrective_actions: [],
    verification_schedule: {
      review_interval: "Quarterly",
      audit_checklist: [],
      sign_off_responsibility: "QA Manager",
    },
    records_generated: [],
    current_stage: "intake",
    awaiting_human_input: false,
    human_decision: null,
    rag_sources: [],
  };
}

export async function mockStartPlan(input: {
  business_name: string;
  product_category: string;
  process_steps: string[];
}): Promise<HACCPState> {
  await delay(900);
  const id = uid();
  const state = baseState(
    id,
    input.business_name,
    input.product_category,
    input.process_steps,
  );
  state.current_stage = "hazard_analyzer";
  state.awaiting_human_input = true;
  state.hazards_identified = input.process_steps.flatMap((step, idx) => [
    {
      name: `Microbial contamination (${step})`,
      category: "biological" as const,
      process_step: step,
      source_in_process: "Inadequate temperature control",
      likelihood: 3 + (idx % 2),
      severity: 4,
      rpn: (3 + (idx % 2)) * 4,
      recommended_control: "Maintain temperature ≤ 5°C; verify hourly.",
      ai_confidence: 0.86,
      citations: ["FSSAI Schedule 4 §3.2", "Codex CAC/RCP 1-1969"],
      user_confirmed: false,
    },
    {
      name: `Chemical residue (${step})`,
      category: "chemical" as const,
      process_step: step,
      source_in_process: "Sanitizer carryover",
      likelihood: 2,
      severity: 3,
      rpn: 6,
      recommended_control: "Triple rinse after CIP, validate ATP swabs.",
      ai_confidence: 0.74,
      citations: ["FSSAI Schedule 4 §5.1"],
      user_confirmed: false,
    },
  ]);
  state.rag_sources = ["FSSAI Schedule 4", "Codex Alimentarius CAC/RCP 1-1969"];
  plans.set(id, state);
  return clone(state);
}

export async function mockResume(
  id: string,
  decision: HumanDecision,
): Promise<HACCPState> {
  await delay(900);
  const state = plans.get(id);
  if (!state) throw new Error("Plan not found");
  state.human_decision = decision;

  if (decision.gate === "hazard_review") {
    state.hazards_identified = (decision.payload.hazards ??
      state.hazards_identified) as HACCPState["hazards_identified"];
    state.hazards_user_confirmed = true;
    state.current_stage = "ccp_determinator";
    state.awaiting_human_input = true;
    state.ccp_candidates = state.hazards_identified.map((h) => ({
      hazard_name: h.name,
      process_step: h.process_step,
      is_ccp: h.rpn >= 9,
      confidence: 0.8,
      decision_tree_path: [
        "Q1: Control measure exists? YES",
        "Q2: Designed to eliminate/reduce? YES",
        "Q3: Could contamination exceed acceptable? " +
          (h.rpn >= 9 ? "YES" : "NO"),
        "Q4: Subsequent step eliminates? NO",
      ],
      reasoning:
        h.rpn >= 9
          ? "High RPN with no downstream kill step — designated CCP."
          : "Hazard is controlled by GMP/PRP rather than a CCP.",
    }));
  } else if (decision.gate === "ccp_review") {
    state.ccps_approved = state.ccp_candidates
      .filter((c) => c.is_ccp)
      .map((c) => ({
        hazard_name: c.hazard_name,
        process_step: c.process_step,
        decision_tree_path: c.decision_tree_path,
        user_override: false,
        override_justification: null,
      }));
    state.ccps_user_approved = true;
    state.current_stage = "limit_fetcher";
    state.awaiting_human_input = true;
    state.critical_limits = Object.fromEntries(
      state.ccps_approved.map((c) => [
        c.hazard_name,
        {
          parameter: "Core temperature",
          min_value: 72,
          max_value: null,
          unit: "°C",
          source_citation: "FSSAI Schedule 4 §6.4",
          user_validated: false,
        },
      ]),
    );
  } else if (decision.gate === "limits_review") {
    state.critical_limits = (decision.payload.critical_limits ??
      state.critical_limits) as HACCPState["critical_limits"];
    state.current_stage = "completed";
    state.awaiting_human_input = false;
    state.monitoring_procedures = state.ccps_approved.map((c) => ({
      ccp_hazard: c.hazard_name,
      method: "Calibrated digital thermometer",
      frequency: "Every batch",
      responsible_person: "Production Supervisor",
      record_format: "Digital log",
    }));
    state.corrective_actions = state.ccps_approved.map((c) => ({
      ccp_hazard: c.hazard_name,
      trigger_condition: "Temperature below critical limit",
      immediate_action: "Hold product, re-cook, re-test",
      root_cause_procedure: "Investigate equipment + retrain",
      personnel: "QA Manager",
    }));
    state.records_generated = ["hazard_analysis.pdf", "ccp_plan.pdf"];
  }
  plans.set(id, state);
  return clone(state);
}

export async function mockGetPlan(id: string) {
  await delay(200);
  const s = plans.get(id);
  if (!s) throw new Error("Plan not found");
  return clone(s);
}

export async function mockChat(message: string): Promise<ChatResponse> {
  await delay(700);
  return {
    answer: `**Per FSSAI Schedule 4**, ${message.slice(0, 60)}... — maintain pasteurization at ≥72°C for 15s, then rapidly cool to ≤5°C. Verify with calibrated thermometers each batch.`,
    sources: [
      "FSSAI Schedule 4 §6.4 (Pasteurization)",
      "Codex CAC/RCP 57-2004 §4.2",
    ],
    confidence: "high",
  };
}

export async function mockLogMonitoring(
  id: string,
  entry: Omit<MonitoringLog, "timestamp" | "is_deviation">,
  limit?: { min?: number | null; max?: number | null },
) {
  await delay(150);
  const is_deviation =
    (limit?.min != null && entry.value < limit.min) ||
    (limit?.max != null && entry.value > limit.max);
  const log: MonitoringLog = {
    ...entry,
    timestamp: new Date().toISOString(),
    is_deviation,
  };
  const list = logs.get(id) ?? [];
  list.push(log);
  logs.set(id, list);
  return {
    status: "recorded" as const,
    is_deviation,
    corrective_action_required: is_deviation
      ? "Hold product and notify QA Manager immediately."
      : null,
    log,
  };
}

export async function mockGetLogs(id: string) {
  await delay(120);
  return { logs: logs.get(id) ?? seedLogs(id) };
}

function seedLogs(id: string): MonitoringLog[] {
  const now = Date.now();
  const seeded: MonitoringLog[] = Array.from({ length: 12 }).map((_, i) => {
    const value = 73 + Math.sin(i) * 1.2 + (i === 5 ? -2.5 : 0);
    return {
      ccp_hazard: "Microbial contamination (Pasteurization)",
      parameter: "Core temperature",
      value: Number(value.toFixed(2)),
      unit: "°C",
      timestamp: new Date(now - (12 - i) * 3600_000).toISOString(),
      is_deviation: value < 72,
      monitored_by: "Auto-seed",
    };
  });
  logs.set(id, seeded);
  return seeded;
}

export async function mockAlerts(): Promise<{
  alerts: ComplianceAlert[];
  compliance_score: number;
  sections?: { title: string; items: [string, boolean][] }[];
}> {
  await delay(250);
  return {
    compliance_score: 88,
    alerts: [
      {
        id: "a1",
        regulatory_source: "FSSAI",
        change_summary:
          "Microbiological standards amendment 2026 — revised Listeria limits for RTE dairy.",
        affected_sections: ["Pasteurization CCP", "Critical Limits"],
        status: "active",
        created_at: new Date().toISOString(),
      },
      {
        id: "a2",
        regulatory_source: "Codex",
        change_summary:
          "Updated guidance on environmental monitoring frequency in cold storage.",
        affected_sections: ["Verification Schedule"],
        status: "active",
        created_at: new Date(Date.now() - 86400_000 * 4).toISOString(),
      },
    ],
    sections: [
      {
        title: "HACCP Prerequisites & Foundation",
        items: [
          ["Business name and category defined", true],
          ["Process flow steps established", true],
        ],
      },
      {
        title: "Hazard Analysis & CCPs",
        items: [
          ["Hazard identification reviewed", true],
          ["Critical Control Points approved", true],
        ],
      },
      {
        title: "Process Controls & Monitoring",
        items: [
          ["Critical limits validated", true],
          ["Monitoring procedures assigned", true],
        ],
      },
      {
        title: "Corrective Actions & Verification",
        items: [
          ["Corrective action procedures ready", true],
          ["Verification schedule planned", true],
        ],
      },
    ],
  };
}

export function mockHealth() {
  return {
    status: "healthy",
    version: "0.1.0-mock",
    services: { api: "ok", postgres: "ok (mock)", chromadb: "ok (mock)" },
  };
}

export function mockListPlans() {
  return Array.from(plans.values()).map((p) => clone(p));
}

function delay(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}
function clone<T>(v: T): T {
  return JSON.parse(JSON.stringify(v));
}

export type { Stage };