/** Shared types for HACCP AI System (frontend ↔ agent API) */

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
  user_confirmed?: boolean;
}

export interface IntakeRequest {
  business_name: string;
  product_category: string;
  process_steps: string[];
  user_id?: string;
}

export interface PlanRunResponse {
  plan_id: string;
  current_stage: string;
  awaiting_human_input: boolean;
  hazards_identified: HazardRecord[];
  rag_sources: string[];
  message: string;
}

export interface ChatRequest {
  message: string;
  product_category?: string;
  stream?: boolean;
}

export interface ChatResponse {
  answer: string;
  sources: string[];
  confidence: "high" | "medium" | "low";
}

export interface RegulatorySearchResult {
  text: string;
  citation: string;
  score: number;
  source_body: SourceBody;
  hazard_types: HazardCategory[];
  product_categories: string[];
}
