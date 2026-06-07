**AI-Powered HACCP Documentation & Regulatory Compliance System**  |  Project Blueprint v1.0

**AI-POWERED HACCP**

**Documentation & Regulatory Compliance**

**Monitoring System**

*Comprehensive Project Blueprint*


|**Subject:** |Bio Safety Engineering|
| -: | :- |
|**Type:** |Major Academic Project|
|**Regulatory Focus:** |FSSAI Schedule 4 + Codex Alimentarius|
|**Version:** |1\.0 – June 2026|


# **Table of Contents**





# **1. Executive Overview**

## **1.1 Project Summary**
The AI-Powered HACCP Documentation and Regulatory Compliance Monitoring System is a proactive, human-in-the-loop, AI-assisted platform purpose-built for food safety engineering. Unlike generic SaaS tools that produce static HACCP templates, this system functions as a collaborative intelligence layer — guiding food business operators (FBOs) through every stage of HACCP plan creation, hazard analysis, CCP monitoring, and audit reporting, while remaining firmly grounded in the FSSAI Schedule 4 regulatory framework and the Codex Alimentarius guidelines adopted by the FAO/WHO.

The platform embeds an agentic AI workflow orchestrated by LangGraph with retrieval-augmented generation (RAG) over curated food safety knowledge bases, real-time regulatory web search, and deliberate human checkpoints at every critical decision point. The result is an engineering product — not a school exercise — that addresses a genuine gap: accessible, intelligent HACCP tooling for small and mid-size food businesses in India.
## **1.2 Problem Statement**
Current HACCP documentation practices in India suffer from three systemic failures:

- Manual & error-prone: Most FBOs, especially small processors, complete HACCP plans on paper or generic spreadsheets, leading to omissions, outdated hazard libraries, and non-conforming CCPs.
- Regulatory blind spots: FSSAI Schedule 4 requirements are updated periodically; most operators are unaware of amendments until an inspection failure.
- No intelligence layer: Existing software (SafetyChain, iAuditor) is expensive, enterprise-only, and not localized for Indian food categories (dairy, ready-to-eat meals, street vendor operations).

This system solves all three directly.
## **1.3 Target Users**

|**User Persona**|**Use Case**|
| :-: | :-: |
|Small FBO Owner|Create first-time FSSAI-compliant HACCP plan, guided step by step|
|Food Safety Manager|Run AI-assisted hazard assessments, set CCP limits, generate audit reports|
|Regulatory Auditor|Review plan completeness, check Schedule 4 compliance, export inspection-ready docs|
|CSE Student / Researcher|Study AI-assisted compliance workflows; demo of LangGraph HITL agents|

## **1.4 Novelty & Differentiators**
This project stands out on the following dimensions:

- FSSAI-native: Regulatory knowledge is not bolted on — it is the primary knowledge corpus. The RAG pipeline is seeded with Schedule 4, FSS Act 2006, and FSSAI inspection checklists.
- Process-type intelligence: The system asks what product category is being produced (e.g., dairy, RTE, fermented, heat-treated) and generates context-specific hazard trees, not generic ones.
- Human-in-the-loop at every critical gate: The agent pauses and presents options whenever a CCP designation, critical limit, or corrective action cannot be determined with high confidence — mimicking the judgment of a senior food safety officer.
- Proactive regulatory surveillance: A background web-search agent checks for FSSAI regulatory updates and flags plan sections that may be out of compliance.
- Audit-ready document generation: Outputs are structured for FSSAI Food Safety Officer inspection checklists — not just generic PDFs.


# **2. Domain Knowledge Foundation**

## **2.1 The 7 Principles of HACCP (Codex Alimentarius)**
The system encodes all seven HACCP principles as distinct workflow stages, each with an AI sub-agent, user interaction gates, and structured data outputs that feed downstream stages.

|**#**|**Principle**|**System Action**|**HITL Gate**|
| :-: | :-: | :-: | :-: |
|**P1**|Hazard Analysis|AI scans process flow, cross-references hazard DB, classifies B/C/P hazards by likelihood and severity|User confirms hazard list; can add, remove, modify|
|**P2**|CCP Determination|Agent applies Codex decision tree; flags candidate CCPs with confidence score|User approves or overrides CCP designations with reasoning|
|**P3**|Critical Limits|RAG retrieves validated limits from FSSAI/ICMR/Codex standards for the product type|User validates limits; custom entries require justification text|
|**P4**|Monitoring Procedures|AI recommends frequency, method, and responsibility assignment for each CCP|User assigns personnel and confirms feasibility|
|**P5**|Corrective Actions|Agent generates corrective action templates per hazard type with FSSAI-compliant wording|User reviews and approves corrective action procedures|
|**P6**|Verification Procedures|AI generates verification schedule and audit checklist aligned to FSSAI inspection matrix|User confirms review intervals and sign-off responsibilities|
|**P7**|Record Keeping|System auto-generates all record templates (FSMS plan, CCP monitoring logs, corrective action logs)|User downloads, reviews, and stores final documentation set|

## **2.2 FSSAI Regulatory Framework**
The Indian regulatory layer adds significant specificity that Codex alone cannot provide. The system's knowledge base covers:

- FSS (Licensing & Registration of Food Businesses) Regulations 2011: Every FBO applying for licensing must maintain a documented FSMS plan complying with Schedule 4.
- Schedule 4 – Six Parts: Part I (food manufacturers), Part II (slaughterhouses), Part III (street vendors), Part IV (food service), Part V (storage & transport), Part VI (catering). The system detects which parts apply to the user's operation.
- FSSAI Inspection Checklist (revised Nov 2022): Compliance (C), Non-Compliance (NC), Partial Compliance (PC) scoring. Asterisk-marked (\*) items are critical — non-observance directly causes NC. The system flags these during plan generation.
- Record retention requirements: FSSAI mandates records be retained for one year or the shelf life of the product, whichever is longer. The system enforces this in generated templates.
## **2.3 Hazard Categories**
The AI hazard identification engine classifies risks across three dimensions per Codex standards:

- Biological hazards: Pathogens (Salmonella, Listeria, E. coli O157:H7, Bacillus cereus), spoilage organisms, allergens, viruses. Severity and likelihood scored on a 1–5 matrix.
- Chemical hazards: Pesticide residues, cleaning agent cross-contamination, heavy metals, food additives above permitted limits, aflatoxins.
- Physical hazards: Metal fragments, glass, bone, plastic, packaging material migration.

For each detected hazard the system outputs: hazard name, category, source in process flow, likelihood score (1–5), severity score (1–5), risk priority number (RPN = L x S), recommended control measure, and whether it constitutes a significant hazard requiring CCP designation.


# **3. System Architecture**

## **3.1 Architecture Philosophy**
The system is designed around three non-negotiable architectural principles:

- Stateful, graph-based agent orchestration: Every HACCP workflow step is a node in a LangGraph state machine, with typed state that persists to a database between sessions. An incomplete plan is never lost.
- Human-in-the-loop as first-class citizen: HITL is not an afterthought. LangGraph's interrupt\_before and interrupt\_after hooks pause execution and surface structured decision requests to the user before any consequential action (CCP designation, critical limit acceptance, report generation) is committed.
- RAG-grounded reasoning: The agent never invents regulatory facts. Every hazard, critical limit, or corrective action it proposes is retrieved from the indexed knowledge base with source attribution. If retrieval confidence is below threshold, the agent says so and asks the user.
## **3.2 High-Level Architecture Diagram**

|**ARCHITECTURE OVERVIEW — Layer Stack**|
| :- |
|┌─────────────────────────────────────────────────────────────────┐|
|│  FRONTEND (Next.js 15 + Vercel AI SDK)                          │|
|│  • Chat-style HITL interface     • Plan Builder Wizard          │|
|│  • CCP Dashboard (real-time)     • Report Preview & Export      │|
|├─────────────────────────────────────────────────────────────────┤|
|│  API GATEWAY (Next.js API Routes / Server Actions)              │|
|│  • Auth middleware (NextAuth)    • SSE streaming (AI responses) │|
|├─────────────────────────────────────────────────────────────────┤|
|│  AGENT LAYER (FastAPI + LangGraph)                              │|
|│  • HACCP Orchestrator Graph      • Hazard Analysis Sub-Agent    │|
|│  • Regulatory Monitor Agent      • Report Generator Agent       │|
|│  • HITL Interrupt Handler        • Plan Validator Agent         │|
|├─────────────────────────────────────────────────────────────────┤|
|│  INTELLIGENCE LAYER                                              │|
|│  • RAG Pipeline (ChromaDB + Embeddings)                         │|
|│  • Web Search Tool (Tavily / Serper)                            │|
|│  • LLM: Claude claude-sonnet-4-20250514 (primary) + claude-haiku (summaries)│|
|├─────────────────────────────────────────────────────────────────┤|
|│  DATA LAYER (PostgreSQL + pgvector)                             │|
|│  • Relational: users, plans, CCPs, records, audit\_logs          │|
|│  • Vector: regulatory\_docs, hazard\_library, precedent\_plans     │|
|│  • LangGraph checkpoint store (plan state persistence)          │|
|└─────────────────────────────────────────────────────────────────┘|

## **3.3 Technology Stack — Full Specification**

|**Layer**|**Technology**|**Rationale**|
| :-: | :-: | :-: |
|**Frontend**|Next.js 15 (App Router)|Server components + streaming UI; native integration with Vercel AI SDK for SSE-based chat|
|**UI Streaming**|Vercel AI SDK (useChat hook)|Handles streaming LLM responses, tool call rendering, and structured human feedback collection in the browser|
|**Styling**|Tailwind CSS + shadcn/ui|Professional component library for dashboard, forms, data tables, and status cards|
|**Agent Orchestration**|LangGraph (Python) on FastAPI|State machine with typed HACCPState, conditional edges, interrupt nodes for HITL, and PostgreSQL checkpointer for plan persistence|
|**LLM**|Anthropic Claude (claude-sonnet-4-20250514 / Haiku)|Sonnet for complex hazard reasoning and report generation; Haiku for fast classification and routing decisions|
|**RAG / Vector DB**|ChromaDB + pgvector|ChromaDB for fast embedding retrieval during hazard analysis; pgvector on PostgreSQL for structured regulatory document search with metadata filters|
|**Embeddings**|OpenAI text-embedding-3-small|Cost-effective, high-quality embeddings; chunks stored with source (FSSAI/Codex/FDA), section, and amendment-date metadata|
|**Web Search**|Tavily Search API|Regulatory monitoring agent uses Tavily to search fssai.gov.in and food safety news for amendment alerts; results summarized and diff-checked against stored plan|
|**Primary DB**|PostgreSQL 16|Relational store for users, HACCP plans, CCP records, monitoring logs, and corrective action events. pgvector extension for hybrid search|
|**Auth**|NextAuth.js v5 (Auth.js)|JWT sessions, Google OAuth + email/password. Role-based access: owner, manager, auditor|
|**Backend API**|FastAPI (Python 3.12)|Agent graph endpoints, SSE streaming, webhook for background regulatory checks. Async-native for non-blocking agent execution|
|**Task Queue**|Celery + Redis|Background jobs: regulatory update checks (daily cron), report PDF generation, email alerts for CCP deviations|
|**PDF Export**|WeasyPrint / Puppeteer|Renders FSSAI-formatted HACCP plan PDFs from Jinja2 HTML templates. Audit-ready output with page numbers, headers, and digital signature fields|
|**Deployment**|Vercel (frontend) + Render/Railway (FastAPI)|Vercel handles Next.js edge deployment; FastAPI deployed as containerized service. Suitable for project demo and real-world SME use|
|**Observability**|LangSmith|Traces every agent step, tool call, retrieval, and HITL pause. Essential for debugging multi-step LangGraph workflows and evaluating retrieval quality|


# **4. LangGraph Agent Architecture**

## **4.1 HACCP Orchestrator Graph**
The core of the system is a LangGraph StateGraph named HACCPOrchestratorGraph. It encodes the entire HACCP workflow as a directed graph with typed state, conditional routing, and interrupt nodes that pause execution for human review.
### **4.1.1 HACCPState — Typed State Schema**

|**HACCPState (TypedDict + Pydantic validation)**|
| :- |
|class HACCPState(TypedDict):|
|`    `# Identity|
|`    `plan\_id: str               # UUID persisted to PostgreSQL|
|`    `user\_id: str|
|`    `business\_name: str|
|`    `product\_category: str      # e.g. 'dairy\_pasteurized'|
|`    `process\_steps: list[str]   # user-defined flow diagram steps|
||
|`    `# P1 – Hazard Analysis|
|`    `hazards\_identified: list[HazardRecord]|
|`    `hazards\_user\_confirmed: bool|
||
|`    `# P2 – CCP Determination|
|`    `ccp\_candidates: list[CCPCandidate]|
|`    `ccps\_approved: list[CCP]|
|`    `ccps\_user\_approved: bool|
||
|`    `# P3–P7 – Subsequent stages|
|`    `critical\_limits: dict[str, CriticalLimit]|
|`    `monitoring\_procedures: list[MonitoringProcedure]|
|`    `corrective\_actions: list[CorrectiveAction]|
|`    `verification\_schedule: VerificationSchedule|
|`    `records\_generated: list[str]|
||
|`    `# Control flow|
|`    `current\_stage: str         # tracks graph position|
|`    `awaiting\_human\_input: bool|
|`    `human\_decision: Optional[HumanDecision]|
|`    `messages: list[BaseMessage]   # conversation history|
|`    `rag\_sources: list[str]         # citations for UI display|

### **4.1.2 Graph Nodes**
Each node is a Python async function that receives the full HACCPState, performs its action, and returns a partial state update.

|**Node Name**|**Responsibility**|**Type**|
| :-: | :-: | :-: |
|intake\_processor|Collects business name, product category, and process flow from user. Validates completeness.|Input Collection|
|hazard\_analyzer|RAG retrieval over hazard library + LLM reasoning. Returns ranked list of hazards with B/C/P classification, likelihood, and severity scores.|AI Analysis|
|hitl\_hazard\_review|INTERRUPT NODE. Presents hazard list to user. User can approve, delete, add custom hazards, or request AI to re-analyze a specific step.|HITL Gate|
|ccp\_determinator|Applies Codex 2020 decision tree to each significant hazard. Outputs CCP candidates with confidence score and decision tree path.|AI Analysis|
|hitl\_ccp\_review|INTERRUPT NODE. User approves or overrides CCP designations. Overrides require a text justification stored in audit log.|HITL Gate|
|critical\_limit\_fetcher|RAG retrieval for validated critical limits from FSSAI Schedule 4, ICMR guidelines, and Codex product-specific standards.|RAG + AI|
|hitl\_limits\_review|INTERRUPT NODE. User validates each critical limit. Custom limits require scientific justification text.|HITL Gate|
|monitoring\_designer|AI generates monitoring procedure for each approved CCP: method, frequency, responsibility, records format.|AI Generation|
|corrective\_action\_gen|Generates FSSAI-compliant corrective action procedures. Templates are product-category and hazard-type specific.|AI Generation|
|verification\_planner|Creates verification schedule aligned to FSSAI inspection matrix. Generates internal audit checklist.|AI Generation|
|record\_generator|Auto-generates all document templates: FSMS plan, CCP monitoring logs, corrective action log, training records.|Document Gen|
|plan\_validator|Final compliance check. Runs completeness checklist against FSSAI Schedule 4. Flags any missing mandatory elements.|Validation|
|report\_generator|Compiles complete HACCP Plan document (PDF + structured JSON). Includes all HITL decisions with audit trail.|Output|

### **4.1.3 Conditional Edges & Routing Logic**
LangGraph conditional edges implement the decision logic that makes the graph intelligent rather than linear:

- After hazard\_analyzer: route to hitl\_hazard\_review (always — every hazard list requires human confirmation).
- After hitl\_hazard\_review: if hazards\_user\_confirmed is True, route to ccp\_determinator. If user requested re-analysis, loop back to hazard\_analyzer with updated context.
- After ccp\_determinator: if confidence of any CCP candidate is below 0.75, route to hitl\_ccp\_review with an explicit uncertainty flag. Always route to hitl\_ccp\_review.
- After plan\_validator: if compliance\_gaps > 0, route back to the relevant stage node with gap context injected into state. If clean, route to report\_generator.

This graph structure means the agent can loop, revisit, and refine — behaving like a knowledgeable food safety consultant rather than a linear form wizard.
## **4.2 Regulatory Monitoring Sub-Agent**
A separate LangGraph agent (RegMonitorGraph) runs as a background process on a daily schedule. It:

1. Queries the FSSAI website and regulatory news sources using Tavily search for any amendments, new orders, or updated circulars.
1. Summarizes findings using Claude and compares them against the user's stored HACCP plan using a semantic diff check.
1. If a relevant change is detected, it generates a 'Compliance Alert' — a structured diff showing which plan sections may be affected and what action is recommended.
1. The alert is pushed to the user's dashboard and optionally sent via email.

This is the proactive compliance monitoring capability — the system does not wait for the user to ask. It watches regulations so the operator does not have to.
## **4.3 RAG Pipeline Design**
### **4.3.1 Knowledge Base Corpus**
The RAG knowledge base is the foundation of the system's regulatory intelligence. It is seeded with:

- FSSAI Schedule 4 (all six parts, revised editions up to 2024)
- FSS (Licensing & Registration of Food Businesses) Regulations 2011 and amendments
- FSSAI Inspection Checklists (revised November 2022) — all sector variants
- Codex Alimentarius General Principles of Food Hygiene (CXC 1-1969, Rev. 2020)
- FDA HACCP Principles & Application Guidelines (NACMCF 1997, updated)
- FAO/WHO Hazard Library: biological, chemical, physical hazards by food category
- ICMR Dietary Guidelines and microbiological standards for Indian food products
- FSSAI product-specific standards (dairy, RTE, meat, aquaculture, street food)
### **4.3.2 Chunking & Embedding Strategy**
Documents are chunked with 1,500-character windows and 300-character overlap to preserve regulatory context across clause boundaries. Each chunk is stored with structured metadata:

- source\_body: 'FSSAI' | 'Codex' | 'FDA' | 'ICMR'
- document\_title and section\_heading for citation generation
- amendment\_date for temporal relevance filtering
- product\_categories: list of applicable food categories for targeted retrieval
- hazard\_types: list of hazard categories mentioned (for hazard-specific retrieval)

This metadata allows the retrieval step to apply filters — e.g., 'retrieve only FSSAI-sourced chunks about dairy biological hazards updated after January 2023' — dramatically improving precision over unfiltered similarity search.


# **5. Database Design**

## **5.1 Database Selection Rationale**
PostgreSQL 16 with the pgvector extension is the single database for both relational and vector data. This is the recommended architecture for this project for the following reasons:

- Unified system: No synchronization overhead between a separate vector store and relational DB. Regulatory chunks, plan records, and user data live in the same ACID-compliant system.
- Hybrid search: pgvector supports both cosine similarity search on embeddings and standard SQL filters — enabling queries like 'find FSSAI chunks about dairy hazards most similar to this process step description, ordered by amendment\_date DESC'.
- pgvector is proven at production scale and integrates natively with LangChain/LangGraph's PostgreSQL checkpointer for plan state persistence.

ChromaDB is used as a fast, in-memory retrieval layer during active agent sessions. At document ingestion time, chunks are written to both ChromaDB (for fast similarity search) and PostgreSQL/pgvector (for persistent, auditable storage with full metadata).
## **5.2 Relational Schema (Key Tables)**

|**Table**|**Key Columns**|**Purpose**|
| :-: | :-: | :-: |
|users|id, email, role, org\_id|Auth and role-based access control (owner, manager, auditor)|
|organizations|id, name, fssai\_license\_no, product\_categories|FBO profile; FSSAI license number drives regulatory context|
|haccp\_plans|id, org\_id, status, product\_category, created\_at, version|Master plan record. Status: draft | in\_progress | complete | under\_review|
|process\_steps|id, plan\_id, step\_name, step\_order, description|User-defined process flow diagram steps|
|hazards|id, plan\_id, step\_id, category, name, likelihood, severity, rpn, ai\_confidence, user\_confirmed|Identified hazards with AI scores and user confirmation status|
|critical\_control\_points|id, plan\_id, hazard\_id, step\_id, decision\_tree\_path, user\_override, override\_justification|Approved CCPs with full decision audit trail including any user overrides|
|critical\_limits|id, ccp\_id, parameter, min\_value, max\_value, unit, source\_citation, user\_validated|Validated critical limits with regulatory source citations|
|monitoring\_procedures|id, ccp\_id, method, frequency, responsible\_person, record\_format|Monitoring schedule for each CCP|
|corrective\_actions|id, ccp\_id, trigger\_condition, immediate\_action, root\_cause\_procedure, personnel|Corrective action procedures triggered on CCP deviation|
|audit\_events|id, plan\_id, user\_id, event\_type, old\_value, new\_value, timestamp, ip\_address|Immutable audit log of every human decision, AI suggestion, and plan modification|
|compliance\_alerts|id, org\_id, regulatory\_source, change\_summary, affected\_sections, status, created\_at|Regulatory update alerts generated by the background monitoring agent|
|regulatory\_chunks|id, source\_body, document\_title, section, text, embedding vector(1536), amendment\_date, product\_categories|RAG knowledge base — pgvector column enables hybrid similarity + filter search|
|langgraph\_checkpoints|thread\_id, checkpoint\_id, state\_json, created\_at|LangGraph plan state checkpoints enabling session resume and state time-travel|


# **6. Feature Specifications & UI/UX Design**

## **6.1 Module 1 — Guided HACCP Plan Creation**
The Plan Builder is the primary user journey. It presents as a side-by-side interface: a conversational AI assistant on the right, and a structured plan-building canvas on the left that fills in real time as the agent works through each HACCP stage.
### **UI Components:**
- Progress stepper: 7 steps (one per HACCP principle) with visual completion status.
- Process Flow Builder: Drag-and-drop step editor where users map their production process (receiving → storage → preparation → cooking → cooling → packaging → dispatch). Each step becomes a node in the AI's hazard analysis.
- AI chat panel: Streaming responses from the agent. When an HITL gate is reached, the chat freezes and a structured decision card appears — not a text field, but a rendered form with checkboxes, sliders, and text inputs matching the decision type.
- Auto-save indicator: Every state update persists to the PostgreSQL LangGraph checkpoint store, so users can close the browser and resume exactly where they left off.
## **6.2 Module 2 — Automated Hazard Assessment**
This is the AI's most knowledge-intensive function. After the user defines the process flow, the hazard\_analyzer node fires and:

1. Performs a RAG retrieval for each process step: 'What biological, chemical, and physical hazards are associated with [step\_name] in [product\_category] production?'
1. Cross-references the Codex hazard library, FSSAI product standards, and precedent HACCP plans from the same product category.
1. Outputs a structured Hazard Register table in the UI, with each row showing: Hazard Name | Category | Process Step | Likelihood (1–5) | Severity (1–5) | RPN | Recommended Control | AI Confidence.
1. Each row has inline edit controls. The user can accept (checkmark), reject (X), modify parameters, or add a custom hazard.
1. When the user submits the confirmed hazard list, the HITL gate is cleared and the graph proceeds to CCP determination.

The Codex 2020 CCP Decision Tree is rendered interactively — the user can see the exact decision tree path the AI followed for each hazard, and override any branch with a justification note.
## **6.3 Module 3 — CCP Monitoring Dashboard**
After the HACCP plan is complete, the system transitions from plan-building to operational monitoring. The CCP Dashboard is a real-time operational screen that enables food safety managers to:

- Log monitoring records: For each CCP, a data entry form with the exact parameters defined in the plan (temperature, pH, time, etc.) with acceptable range indicators (green/amber/red).
- Deviation alerts: When an entered value falls outside the critical limit, the system immediately flags it in red, triggers the corrective action protocol, and logs a deviation event in the audit trail.
- Trend visualization: Line charts for each CCP monitoring parameter over time, enabling managers to spot drift toward critical limits before a violation occurs.
- Responsibility tracking: Each monitoring record requires a named responsible person and timestamp — matching FSSAI record-keeping requirements.
## **6.4 Module 4 — Report Generation**
The report generator compiles a fully structured HACCP plan document from the database. Reports are generated in two formats:

- PDF (FSSAI-formatted): Structured per the FSSAI inspection checklist categories. Includes cover page, hazard register, CCP summary table, monitoring procedures, corrective action procedures, verification schedule, and all record templates. Suitable for submission to FSSAI Food Safety Officers.
- JSON export: Machine-readable plan data for integration with other quality management systems.

The PDF uses a branded layout with the organization's name, FSSAI license number, and plan version/date, along with space for authorized digital signatures. The system enforces the FSSAI requirement of clearly marking asterisk (\*) critical items.
## **6.5 Module 5 — Regulatory Compliance Monitor**
This module surfaces the proactive surveillance outputs. The dashboard shows:

- Compliance Status: A green/amber/red card per FSSAI Schedule 4 section, indicating whether the current plan is fully compliant, partially compliant, or flagged for review.
- Regulation Alerts Feed: Timestamped alerts from the background monitoring agent, each showing the regulatory change, affected plan sections, and recommended action.
- Compliance Score: An aggregate percentage score derived from the completeness check across all Schedule 4 mandatory elements.
- Amendment History: A timeline of all regulatory changes detected since the plan was created.


# **7. Phase-Wise Development Roadmap**

The project is structured in four phases, each producing a working, demonstrable deliverable. Each phase is designed to be independently presentable.

## **Phase 1 — Foundation & Intelligence Core  (Weeks 1–3)**

|**Phase 1 Goals**|
| :- |
|Goal: Working RAG pipeline + basic LangGraph agent. Demonstrable: AI can answer HACCP questions from FSSAI documents.|
||
|1\. Environment Setup|
|`   `• Next.js 15 project scaffolded, FastAPI app created, PostgreSQL instance configured|
|`   `• pgvector extension installed, ChromaDB initialized|
|`   `• LangSmith project created for observability|
||
|2\. Knowledge Base Construction|
|`   `• Download and parse: FSSAI Schedule 4 (all parts), Codex CXC 1-1969 Rev 2020, FSSAI inspection checklists|
|`   `• Implement chunking pipeline: 1500-char chunks, 300-char overlap, metadata tagging|
|`   `• Embed with text-embedding-3-small, store in ChromaDB + pgvector|
|`   `• Validate retrieval quality: test 20 domain-specific queries, measure precision|
||
|3\. Basic LangGraph Agent|
|`   `• Implement HACCPState TypedDict|
|`   `• Build intake\_processor and hazard\_analyzer nodes|
|`   `• Connect RAG retrieval as a LangChain tool called by the agent|
|`   `• Test: given a product category and process step, does the agent return relevant hazards with citations?|
||
|4\. Minimal UI|
|`   `• Next.js app with NextAuth login|
|`   `• Simple chat interface using Vercel AI SDK useChat hook|
|`   `• Streaming agent responses visible in browser|
||
|Milestone: Demo a query like 'What are the biological hazards in pasteurization of milk per FSSAI?' receiving a cited, accurate answer.|

## **Phase 2 — Full Agent Graph + HITL  (Weeks 4–6)**

|**Phase 2 Goals**|
| :- |
|Goal: Complete LangGraph HACCP workflow with all HITL gates. Demonstrable: Full guided plan creation for one product category.|
||
|1\. Complete Graph Implementation|
|`   `• Implement all 12 nodes (see Section 4.1.2)|
|`   `• Implement conditional routing logic with interrupt\_before on all HITL nodes|
|`   `• Configure PostgreSQL LangGraph checkpointer for plan state persistence|
|`   `• Implement Codex 2020 CCP decision tree as a structured tool|
||
|2\. HITL Frontend Components|
|`   `• Hazard Review Card: table with inline approve/reject/edit controls|
|`   `• CCP Approval Card: decision tree visualization with override input|
|`   `• Critical Limit Card: parameter editor with source citation display|
|`   `• Human decision captured, validated, and injected back into LangGraph state via /resume API endpoint|
||
|3\. Process Flow Builder|
|`   `• Drag-and-drop step builder in Next.js (using @dnd-kit)|
|`   `• Steps stored in haccp\_plans.process\_steps table|
|`   `• Steps passed to agent as structured context|
||
|4\. Database Schema|
|`   `• All tables from Section 5.2 created with migrations (Alembic for FastAPI side)|
|`   `• Audit event logging middleware implemented|
||
|Milestone: Complete end-to-end HACCP plan creation for 'Pasteurized Milk' product, with all 7 HITL gates traversed and plan persisted.|

## **Phase 3 — Monitoring, Reports & Compliance  (Weeks 7–9)**

|**Phase 3 Goals**|
| :- |
|Goal: Operational monitoring dashboard, PDF report generation, and regulatory alert system.|
||
|1\. CCP Monitoring Dashboard|
|`   `• Monitoring record entry forms (per CCP, per plan)|
|`   `• Deviation detection and alert logic|
|`   `• Recharts trend visualizations for each monitored parameter|
|`   `• Corrective action trigger and logging flow|
||
|2\. Report Generation|
|`   `• Jinja2 HTML templates for FSSAI-formatted HACCP plan|
|`   `• WeasyPrint PDF rendering pipeline triggered from FastAPI|
|`   `• Celery task for async PDF generation with webhook notification|
|`   `• JSON export endpoint for structured plan data|
||
|3\. Regulatory Monitoring Agent|
|`   `• RegMonitorGraph LangGraph implementation|
|`   `• Tavily search integration for FSSAI website surveillance|
|`   `• Semantic diff tool: compare new regulatory text against stored plan sections|
|`   `• Celery daily cron trigger|
|`   `• Compliance alert stored in DB and displayed on dashboard|
||
|4\. Compliance Score Engine|
|`   `• Schedule 4 completeness checklist mapped to plan fields|
|`   `• Scoring logic: mandatory fields (4 marks each), standard fields (2 marks)|
|`   `• Compliance status card with section-level breakdown|
||
|Milestone: Generate a complete, FSSAI-formatted PDF HACCP plan. Simulate a regulatory update and verify alert is generated.|

## **Phase 4 — Polish, Testing & Documentation  (Weeks 10–12)**

|**Phase 4 Goals**|
| :- |
|Goal: Production-ready presentation quality. Full test coverage. Final documentation.|
||
|1\. Multi-Product Support|
|`   `• Extend hazard library and critical limits for: RTE meals, dairy fermented, street food/catering, packaged water|
|`   `• Schedule 4 part detection based on FBO operation type|
||
|2\. UI Polish|
|`   `• Landing page with product category selector and onboarding flow|
|`   `• shadcn/ui component audit — consistent design system|
|`   `• Mobile-responsive layout for dashboard views|
|`   `• Loading states, error boundaries, and retry logic for all agent calls|
||
|3\. Testing|
|`   `• Unit tests: RAG retrieval precision on FSSAI-specific queries|
|`   `• Integration tests: full plan creation workflow (pytest + FastAPI TestClient)|
|`   `• End-to-end tests: Playwright for frontend HITL flows|
|`   `• LangSmith evaluation sets for agent decision quality|
||
|4\. Documentation|
|`   `• API reference (auto-generated from FastAPI OpenAPI spec)|
|`   `• Architecture decision records (ADRs) for key design choices|
|`   `• User manual covering all 5 modules|
|`   `• Project presentation deck and demo script|
||
|Milestone: Live demo of complete system. Full HACCP plan creation → CCP monitoring → regulatory alert → PDF report for a food business scenario.|


# **8. Project Repository Structure**

|**Monorepo Layout**|
| :- |
|haccp-system/|
|├── apps/|
|│   ├── web/                        # Next.js 15 frontend|
|│   │   ├── app/|
|│   │   │   ├── (auth)/             # login, register pages|
|│   │   │   ├── dashboard/          # main app layout|
|│   │   │   │   ├── plan/[id]/      # plan builder + chat|
|│   │   │   │   ├── monitor/        # CCP monitoring dashboard|
|│   │   │   │   ├── reports/        # report generation & history|
|│   │   │   │   └── compliance/     # regulatory monitor|
|│   │   │   └── api/|
|│   │   │       ├── chat/route.ts   # Vercel AI SDK streaming endpoint|
|│   │   │       └── auth/[...nextauth]/route.ts|
|│   │   ├── components/|
|│   │   │   ├── hitl/               # HazardReviewCard, CCPCard, LimitCard|
|│   │   │   ├── plan-builder/       # ProcessFlowBuilder, ProgressStepper|
|│   │   │   ├── dashboard/          # CCPMonitorChart, DeviationAlert|
|│   │   │   └── ui/                 # shadcn/ui components|
|│   │   └── lib/|
|│   │       ├── agent-client.ts     # FastAPI agent API calls|
|│   │       └── db.ts               # Prisma client|
|│   │|
|│   └── agent/                      # FastAPI + LangGraph backend|
|│       ├── main.py                 # FastAPI app, CORS, routes|
|│       ├── graphs/|
|│       │   ├── haccp\_graph.py      # HACCPOrchestratorGraph|
|│       │   └── reg\_monitor.py      # RegMonitorGraph|
|│       ├── nodes/|
|│       │   ├── intake.py|
|│       │   ├── hazard\_analyzer.py|
|│       │   ├── ccp\_determinator.py|
|│       │   ├── limit\_fetcher.py|
|│       │   ├── monitoring\_designer.py|
|│       │   ├── corrective\_action\_gen.py|
|│       │   ├── record\_generator.py|
|│       │   └── plan\_validator.py|
|│       ├── rag/|
|│       │   ├── ingest.py           # Document chunking + embedding pipeline|
|│       │   ├── retriever.py        # Hybrid ChromaDB + pgvector retrieval|
|│       │   └── sources/            # Raw regulatory PDFs|
|│       ├── tools/|
|│       │   ├── decision\_tree.py    # Codex 2020 CCP decision tree|
|│       │   ├── web\_search.py       # Tavily search wrapper|
|│       │   └── pdf\_generator.py    # WeasyPrint report generation|
|│       ├── models/|
|│       │   └── state.py            # HACCPState, HazardRecord, CCP types|
|│       ├── db/|
|│       │   ├── models.py           # SQLAlchemy ORM models|
|│       │   └── migrations/         # Alembic migrations|
|│       └── workers/|
|│           └── reg\_monitor\_task.py # Celery daily cron task|
|│|
|├── packages/|
|│   └── shared-types/               # Shared TypeScript types (plan, hazard, CCP)|
|│|
|├── docs/|
|│   ├── architecture/               # ADRs and architecture diagrams|
|│   ├── api/                        # OpenAPI spec exports|
|│   └── user-manual/|
|│|
|└── docker-compose.yml              # PostgreSQL + Redis + ChromaDB for local dev|


# **9. Risks, Constraints & Mitigations**

|**Risk**|**Impact**|**Mitigation**|
| :-: | :-: | :-: |
|RAG hallucination on regulatory facts|**HIGH**|Every agent output grounded in retrieved chunks. If retrieval confidence < threshold, agent explicitly states uncertainty and asks user to verify. Source citations shown in UI for every regulatory claim.|
|LLM API cost during development|**MEDIUM**|Use Claude Haiku for classification and routing decisions; Sonnet only for generation-heavy nodes. RAG pre-filtering reduces token consumption by limiting context to relevant chunks.|
|FSSAI regulations change during project|**MEDIUM**|Knowledge base documents are versioned with amendment\_date. The regulatory monitor agent is designed specifically to detect and surface these changes. Documents can be re-ingested without restarting the system.|
|LangGraph HITL complexity in full-stack integration|**HIGH**|Use LangGraph's thread\_id + checkpoint system. Frontend calls /resume endpoint with user decision; FastAPI resumes the paused graph from the checkpoint. This pattern is well-documented and tested.|
|Plan state loss on server restart|**MEDIUM**|PostgreSQL LangGraph checkpointer persists full state. No in-memory-only state. Every node completion writes to DB before acknowledging the frontend.|
|PDF generation performance|**LOW**|PDF generation is offloaded to a Celery background task. User receives a 'generating...' status and a webhook notification when the PDF is ready for download.|
|Scope creep beyond academic project timeline|**MEDIUM**|Phases 1–2 are the minimum viable project (MVP). Phases 3–4 are enhancement phases. The project can be submitted at Phase 2 completion if time is constrained, with Phase 3–4 as future scope.|


# **10. Academic Novelty & Contribution Summary**

This section explicitly articulates the academic and engineering contributions of this project for the purpose of evaluation and presentation.

## **10.1 Technical Novelty**
- Application of LangGraph HITL agent architecture to a food safety domain: This is a domain-specific application of a state-of-the-art agentic AI orchestration pattern to a regulatory compliance problem that has not been publicly demonstrated in the FSSAI/Indian food safety context.
- RAG-grounded hazard analysis: Rather than relying on static HACCP templates, the system performs dynamic hazard retrieval from a curated, indexed regulatory corpus. The retrieval is metadata-filtered by product category, hazard type, and document amendment date — a more sophisticated retrieval strategy than standard cosine-similarity-only RAG.
- Proactive regulatory surveillance agent: The background RegMonitorGraph agent demonstrates how an agentic system can maintain temporal awareness of a changing regulatory environment — a capability not present in any existing commercial HACCP software for Indian FBOs.
- Structured HITL with audit trail: The system does not just ask the user 'do you agree?' — it presents structured decision cards with AI confidence scores, regulatory citations, and decision tree paths, and records every human override with justification text into an immutable audit log.
## **10.2 Domain Contribution**
- Accessible FSSAI compliance tooling: The platform makes HACCP documentation accessible to small FBOs who cannot afford enterprise food safety software, directly addressing a gap in the Indian food safety ecosystem.
- FSSAI-native design: The system treats FSSAI Schedule 4 as a first-class requirement specification, not an afterthought. The compliance scoring engine maps plan completeness directly to FSSAI Food Safety Officer inspection criteria.
## **10.3 Engineering Contribution**
- Full-stack AI system with agent backend: Demonstrates integration of Next.js + Vercel AI SDK + FastAPI + LangGraph as a production-grade architecture pattern for human-in-the-loop AI applications.
- Multi-DB strategy: The pgvector + ChromaDB hybrid storage strategy demonstrates practical trade-offs between retrieval speed (ChromaDB for active sessions) and persistence + hybrid search (pgvector for audit and temporal queries).


*End of Project Blueprint v1.0  |  AI-Powered HACCP Documentation & Regulatory Compliance Monitoring System*
Page  [Page]   |  Confidential – Academic Project
