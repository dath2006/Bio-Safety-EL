import * as mock from "./mock";
import type {
  ChatResponse,
  ComplianceAlert,
  HACCPState,
  HumanDecision,
  MonitoringLog,
} from "./types";

const BASE = import.meta.env.VITE_AGENT_API_URL ?? "";
const USE_MOCK =
  (import.meta.env.VITE_USE_MOCK ?? "true").toString() !== "false" || !BASE;

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

function mapState(state: HACCPState): HACCPState {
  let stage = state.current_stage;
  if (stage === "hazard_review" as any) stage = "hazard_analyzer";
  if (stage === "ccp_review" as any) stage = "ccp_determinator";
  if (stage === "limits_review" as any) stage = "limit_fetcher";
  return {
    ...state,
    current_stage: stage,
  };
}

export const api = {
  useMock: USE_MOCK,

  async health() {
    if (USE_MOCK) return mock.mockHealth();
    return req<{ status: string }>("/health");
  },

  async stats(): Promise<{
    total_plans: number;
    active_plans: number;
    completed_plans: number;
    rag_chunks: number;
    categories_covered: number;
  }> {
    if (USE_MOCK) {
      return {
        total_plans: 3,
        active_plans: 1,
        completed_plans: 2,
        rag_chunks: 142,
        categories_covered: 11,
      };
    }
    return req("/api/stats");
  },

  async ingest(): Promise<{
    status: string;
    documents_processed: number;
    chunks_created: number;
  }> {
    if (USE_MOCK) {
      await new Promise((r) => setTimeout(r, 1500));
      return { status: "success", documents_processed: 11, chunks_created: 152 };
    }
    return req("/api/ingest", { method: "POST" });
  },

  async listDocuments(): Promise<{
    documents: Array<{
      filename: string;
      title: string;
      source_body: string;
      amendment_date: string | null;
      product_categories: string[];
      type: "seed" | "custom";
      chunks_count: number;
    }>;
  }> {
    if (USE_MOCK) {
      return {
        documents: [
          {
            filename: "fssai_schedule4_part1_manufacturers.md",
            title: "FSSAI Schedule 4 Part I — Food Manufacturers",
            source_body: "FSSAI",
            amendment_date: "2024-01-01",
            product_categories: ["dairy", "dairy_pasteurized", "rte", "general"],
            type: "seed",
            chunks_count: 24,
          },
          {
            filename: "custom_reg_poultry_2026.md",
            title: "Dynamic Custom Poultry Guidelines 2026",
            source_body: "QA-Custom",
            amendment_date: "2026-02-15",
            product_categories: ["meat"],
            type: "custom",
            chunks_count: 14,
          }
        ]
      };
    }
    return req("/api/documents");
  },

  async uploadDocument(formData: FormData): Promise<{
    status: string;
    message: string;
    ingest_result: any;
  }> {
    if (USE_MOCK) {
      await new Promise((r) => setTimeout(r, 1500));
      return {
        status: "success",
        message: "Document uploaded and indexed successfully.",
        ingest_result: { documents_processed: 12, chunks_created: 110 }
      };
    }
    const res = await fetch(`${BASE}/api/documents/upload`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    return res.json();
  },

  async deleteDocument(filename: string): Promise<any> {
    if (USE_MOCK) return { status: "success" };
    const res = await fetch(`${BASE}/api/documents/${filename}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    return res.json();
  },

  async chat(message: string, product_category: string): Promise<ChatResponse> {
    if (USE_MOCK) return mock.mockChat(message);
    return req("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message, product_category, stream: false }),
    });
  },

  async chatStream(
    message: string,
    product_category: string,
    onChunk: (text: string) => void,
    onMeta: (meta: ChatResponse) => void,
  ): Promise<void> {
    if (USE_MOCK) {
      onMeta({
        answer: "",
        sources: [
          "FSSAI Schedule 4 §6.4 (Pasteurization)",
          "Codex CAC/RCP 57-2004 §4.2",
        ],
        confidence: "high",
      });
      const thinkingParts = [
        "<thinking>\n",
        "Analyzing product category: " + product_category + "\n",
        "Searching FSSAI Schedule 4 and Codex indexes...\n",
        "Extracting pasteurization parameters...\n",
        "Formulating safety response...\n",
        "</thinking>\n",
      ];
      for (const part of thinkingParts) {
        onChunk(part);
        await new Promise((r) => setTimeout(r, 150));
      }
      const answer = `**Per FSSAI Schedule 4**, for the category **${product_category}**, it is essential to maintain thermal processing boundaries (e.g., pasteurization at **≥72°C for 15 seconds**, or equivalent validation). \n\nKey requirements include:\n- Rapid cooling to **≤5°C** post-heat treatment.\n- Continuous recording using calibrated digital probes.\n- Immediate logging of any deviation in the CCP log.`;
      const words = answer.split(" ");
      for (const w of words) {
        onChunk(w + " ");
        await new Promise((r) => setTimeout(r, 40));
      }
      return;
    }

    const response = await fetch(`${BASE}/api/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, product_category }),
    });
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
    const reader = response.body?.getReader();
    if (!reader) throw new Error("Response body not readable");

    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";
      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = line.slice(6);
          if (data === "[DONE]") break;
          if (data.startsWith("METADATA:")) {
            try {
              const meta = JSON.parse(data.slice(9));
              onMeta(meta);
            } catch (e) {
              console.error("Error parsing stream metadata:", e);
            }
          } else {
            const chunk = data.replace(/\\n/g, "\n");
            onChunk(chunk);
          }
        }
      }
    }
  },

  async startPlan(input: {
    business_name: string;
    product_category: string;
    process_steps: string[];
  }): Promise<HACCPState> {
    if (USE_MOCK) return mock.mockStartPlan(input);
    const res = await req<HACCPState>("/api/plans/run", {
      method: "POST",
      body: JSON.stringify(input),
    });
    return mapState(res);
  },

  async resume(id: string, decision: HumanDecision): Promise<HACCPState> {
    if (USE_MOCK) return mock.mockResume(id, decision);
    const res = await req<HACCPState>(`/api/plans/${id}/resume`, {
      method: "POST",
      body: JSON.stringify(decision),
    });
    return mapState(res);
  },

  async getPlan(id: string): Promise<HACCPState> {
    if (USE_MOCK) return mock.mockGetPlan(id);
    const res = await req<HACCPState>(`/api/plans/${id}`);
    return mapState(res);
  },

  async listPlans(): Promise<Array<{
    plan_id: string;
    business_name: string;
    product_category: string;
    status: string;
    current_stage: string;
    created_at: string;
  }>> {
    if (USE_MOCK) return mock.mockListPlans() as any;
    return req("/api/plans");
  },

  async logMonitoring(
    id: string,
    entry: Omit<MonitoringLog, "timestamp" | "is_deviation">,
    limit?: { min?: number | null; max?: number | null },
  ): Promise<{
    status: "recorded";
    is_deviation: boolean;
    corrective_action_required: string | null;
  }> {
    if (USE_MOCK) return mock.mockLogMonitoring(id, entry, limit);
    return req(`/api/plans/${id}/monitoring`, {
      method: "POST",
      body: JSON.stringify(entry),
    });
  },

  async getLogs(id: string): Promise<{ logs: MonitoringLog[] }> {
    if (USE_MOCK) return mock.mockGetLogs(id);
    return req(`/api/plans/${id}/monitoring`);
  },

  async alerts(
    id: string,
  ): Promise<{
    alerts: ComplianceAlert[];
    compliance_score: number;
    sections?: { title: string; items: [string, boolean][] }[];
  }> {
    if (USE_MOCK) return mock.mockAlerts();
    return req(`/api/plans/${id}/alerts`);
  },

  async generatePdf(id: string) {
    if (USE_MOCK) {
      await new Promise((r) => setTimeout(r, 800));
      return { job_id: "job_mock", status: "completed" as const };
    }
    return req(`/api/plans/${id}/generate-pdf`, { method: "POST" });
  },

  pdfUrl(id: string) {
    return `${BASE}/api/plans/${id}/pdf`;
  },

  listPlansLocal() {
    return mock.mockListPlans();
  },
};