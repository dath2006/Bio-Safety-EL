export type HazardCategory = "biological" | "chemical" | "physical";
export type SourceBody = "FSSAI" | "Codex" | "FDA" | "ICMR";
export type PlanStatus = "draft" | "in_progress" | "complete" | "under_review";

export interface HazardRecord {
  name: string;
  category: HazardCategory;
  process_step: string;
  source_in_process?: string;
  likelihood: number;
  severity: number;
  rpn: number;
  recommended_control: string;
  ai_confidence: number;
  citations: string[];
  user_confirmed: boolean;
}

export interface CCPCandidate {
  hazard_name: string;
  process_step: string;
  is_ccp: boolean;
  confidence: number;
  decision_tree_path: string[];
  reasoning: string;
}

export interface CCP {
  hazard_name: string;
  process_step: string;
  decision_tree_path: string[];
  user_override: boolean;
  override_justification?: string | null;
}

export interface CriticalLimit {
  parameter: string;
  min_value?: number | null;
  max_value?: number | null;
  unit: string;
  source_citation: string;
  user_validated: boolean;
}

export interface MonitoringProcedure {
  ccp_hazard: string;
  method: string;
  frequency: string;
  responsible_person: string;
  record_format: string;
}

export interface CorrectiveAction {
  ccp_hazard: string;
  trigger_condition: string;
  immediate_action: string;
  root_cause_procedure: string;
  personnel: string;
}

export interface VerificationSchedule {
  review_interval: string;
  audit_checklist: string[];
  sign_off_responsibility: string;
}

export interface HumanDecision {
  gate: "hazard_review" | "ccp_review" | "limits_review";
  action: "approve" | "reject" | "modify" | "reanalyze";
  payload: Record<string, any>;
  justification?: string | null;
}

export type Stage =
  | "intake"
  | "hazard_analyzer"
  | "ccp_determinator"
  | "limit_fetcher"
  | "monitoring_designer"
  | "corrective_action_gen"
  | "verification_planner"
  | "record_generator"
  | "plan_validator"
  | "report_generator"
  | "completed";

export interface HACCPState {
  plan_id: string;
  user_id: string;
  business_name: string;
  product_category: string;
  process_steps: string[];
  hazards_identified: HazardRecord[];
  hazards_user_confirmed: boolean;
  ccp_candidates: CCPCandidate[];
  ccps_approved: CCP[];
  ccps_user_approved: boolean;
  critical_limits: Record<string, CriticalLimit>;
  monitoring_procedures: MonitoringProcedure[];
  corrective_actions: CorrectiveAction[];
  verification_schedule: VerificationSchedule;
  records_generated: string[];
  current_stage: Stage;
  awaiting_human_input: boolean;
  human_decision?: HumanDecision | null;
  rag_sources: string[];
}

export interface ComplianceAlert {
  id: string;
  regulatory_source: string;
  change_summary: string;
  affected_sections: string[];
  status: "active" | "resolved";
  created_at: string;
}

export interface ChatResponse {
  answer: string;
  sources: string[];
  confidence: "high" | "medium" | "low";
}

export interface MonitoringLog {
  ccp_hazard: string;
  parameter: string;
  value: number;
  unit?: string;
  timestamp: string;
  is_deviation: boolean;
  monitored_by?: string;
}