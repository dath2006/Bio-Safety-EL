# HACCP AI System — User Manual

**Version:** 1.0 — June 2026  
**System:** AI-Powered HACCP Documentation & Regulatory Compliance Monitoring System  
**Regulatory Scope:** FSSAI Schedule 4 + Codex Alimentarius  

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Module 1 — Regulatory Chat](#module-1--regulatory-chat)
3. [Module 2 — Plan Builder (Guided HACCP Creation)](#module-2--plan-builder)
4. [Module 3 — CCP Monitoring Dashboard](#module-3--ccp-monitoring-dashboard)
5. [Module 4 — Report Generation](#module-4--report-generation)
6. [Module 5 — Regulatory Compliance Monitor](#module-5--regulatory-compliance-monitor)
7. [Knowledge Base Manager](#knowledge-base-manager)
8. [FAQ & Troubleshooting](#faq--troubleshooting)

---

## Getting Started

### Prerequisites

| Service | Default URL | Purpose |
|---------|------------|---------|
| FastAPI Agent | http://localhost:8000 | AI backend + RAG pipeline |
| Vite Frontend | http://localhost:8080 | Web application |
| PostgreSQL | localhost:5432 | Plan data + vector store |
| ChromaDB | localhost:8001 | Fast semantic search |
| Redis | localhost:6379 | Celery task queue |

### Starting the System

```bash
# 1. Start infrastructure
docker compose up -d

# 2. Start the backend agent
cd apps/agent
.venv\Scripts\activate
python main.py

# 3. Start the frontend (in a new terminal)
cd apps/client
npm run dev
```

Access the application at **http://localhost:8080**

---

## Module 1 — Regulatory Chat

**Location:** Dashboard → Regulatory Chat  
**Purpose:** Ask natural language questions about FSSAI Schedule 4, Codex Alimentarius, or general HACCP requirements. The AI retrieves answers directly from the indexed regulatory knowledge base with source citations.

### How to Use

1. Select a **product category** from the dropdown (e.g., "Dairy – Pasteurized Milk")
2. Type your question in the chat box and press Enter or click Send
3. The AI will stream its response in real time
4. Expand the **Sources** section at the bottom of each response to see which regulatory documents were cited

### Example Questions

- *"What are the critical limits for pasteurization of milk per FSSAI Schedule 4?"*
- *"What biological hazards must be considered for ready-to-eat meals?"*
- *"What are FSSAI's requirements for CCP monitoring record retention?"*
- *"Explain the Codex 2020 CCP decision tree steps."*

### Thinking Mode

When the AI is reasoning through complex questions, you will see a collapsible **Thinking** block above the answer. Click to expand and see the AI's reasoning chain.

---

## Module 2 — Plan Builder

**Location:** Dashboard → Plan Builder  
**Purpose:** Create a complete, FSSAI-compliant HACCP plan step by step, guided by the AI agent. Uses a Human-in-the-Loop (HITL) workflow — the AI pauses at each critical decision point and waits for your confirmation.

### Step 1: Business & Product Setup

Fill in:
- **Business Name** — your food business operator name
- **Product Category** — select from the dropdown (dairy, RTE, meat, street food, etc.)
- **Process Flow Steps** — add each step in your production process (e.g., Receiving → Storage → Pasteurisation → Packaging → Dispatch)
  - Use the **Add Step** button to add steps
  - Drag and drop to reorder (on desktop)
  - Click × to remove a step

Click **Start Plan** to begin the AI analysis.

### Step 2: Hazard Review (HITL Gate 1)

The AI will analyse each process step and present a **Hazard Register** table showing:
- Hazard name, category (Biological/Chemical/Physical)
- Process step where the hazard occurs
- Likelihood score (1–5), Severity score (1–5), Risk Priority Number (RPN)
- AI confidence score
- Recommended control measure

**Your actions:**
- ✓ **Approve** hazards that are correct
- ✗ **Reject** hazards that don't apply to your process
- ✏️ **Edit** parameters if you disagree with the AI's assessment
- ➕ **Add Custom Hazard** if you know of a hazard the AI missed

Click **Confirm Hazard List** to proceed to CCP determination.

### Step 3: CCP Determination (HITL Gate 2)

The AI applies the **Codex 2020 CCP Decision Tree** to each significant hazard. You will see:
- Each hazard with the AI's decision tree path
- CCP designation (CCP or not)
- AI confidence score (⚠️ low confidence items are flagged)

**Your actions:**
- Approve or override each CCP designation
- If overriding, enter a justification — this is recorded in the audit trail
- Click **Approve All CCPs** to proceed

### Step 4: Critical Limits (HITL Gate 3)

For each approved CCP, the AI retrieves validated critical limits from FSSAI Schedule 4, ICMR, and Codex standards.

**Your actions:**
- Review each critical limit and its source citation
- Validate limits that are correct (click ✓)
- Enter custom limits if needed — you must provide a scientific justification text
- Click **Confirm Limits** to proceed

### Steps 5–7: Automated Generation

The remaining stages are fully automated:
- **Monitoring Procedures:** AI generates method, frequency, responsible person, and record format for each CCP
- **Corrective Actions:** FSSAI-compliant corrective action procedures for each CCP deviation
- **Verification Schedule:** Internal audit checklist and frequency schedule
- **Record Templates:** All FSMS documentation generated automatically
- **Compliance Validation:** The AI runs a completeness check against Schedule 4 requirements

When complete, the plan is saved and available in the **Reports** module.

---

## Module 3 — CCP Monitoring Dashboard

**Location:** Dashboard → CCP Monitor  
**Purpose:** Real-time operational monitoring of each Critical Control Point. Log parameter readings, detect deviations, visualise trends, and trigger corrective actions.

### Plan Selection

Select your active HACCP plan from the dropdown at the top. The dashboard will load all CCPs defined in that plan.

### Multi-CCP Overview Strip

A summary bar at the top shows all CCPs at a glance with colour-coded status badges:
- 🟢 **In control** — last reading was within critical limits
- 🔴 **Deviation** — last reading exceeded a critical limit (badge pulses to draw attention)

Click any CCP badge to jump to that CCP's detailed view.

### Logging a Measurement

1. Click the CCP card you want to log a reading for
2. In the **Record measurement** panel on the right, enter the measured value
3. Click **Submit reading**
4. If the value is within limits: ✅ Recorded — no alert
5. If the value breaches a critical limit: 🚨 **Deviation alert** — the corrective action procedure appears immediately

### Trend Chart

The line chart shows the history of readings for the selected CCP parameter. Reference lines mark the minimum and maximum critical limits. Use this to spot drift before a deviation occurs.

### Export CSV

Click **Export CSV** to download all monitoring logs for the selected plan as a CSV file. Suitable for record-keeping and FSSAI audit submission.

---

## Module 4 — Report Generation

**Location:** Dashboard → Reports  
**Purpose:** Generate audit-ready PDF HACCP plan documents formatted per FSSAI inspection standards, plus JSON exports for QMS integration.

### Generating a PDF

1. Locate your completed plan in the list
2. Click **Generate PDF**
3. The backend renders the PDF (takes 5–10 seconds)
4. When ready, the button changes to **Download PDF** — click to download

### PDF Contents

The generated PDF includes:
- Cover page with business name, product category, plan ID, generation date
- Section 1: Process Flow Diagram Steps
- Section 2: Hazard Analysis Table (all identified hazards with RPN scores)
- Section 3: Approved Critical Control Points with decision tree paths
- Section 4: Process Control Specifications (critical limits, monitoring procedures, corrective actions per CCP)
- Section 5: Verification Schedule
- Space for authorised signatures (Food Safety Manager + Food Safety Officer)

### JSON Export

Click the **JSON** icon to preview the structured plan data, or click the download arrow to export as a JSON file. Suitable for integration with external quality management systems.

### Plan Progress Bar

Plans that are still in progress show a progress bar indicating which stage they've completed. You must complete all 7 HACCP stages before PDF generation is enabled.

---

## Module 5 — Regulatory Compliance Monitor

**Location:** Dashboard → Compliance  
**Purpose:** Monitor FSSAI Schedule 4 audit readiness for each plan and track regulatory changes via the proactive surveillance system.

### Compliance Score Gauge

The circular gauge shows an aggregate compliance score (0–100%) for the selected plan:
- **≥90%:** Excellent — audit ready
- **70–89%:** Good — minor actions needed
- **50–69%:** Needs Action — review flagged sections
- **<50%:** Non-compliant — significant gaps

### Section Coverage Accordion

Expand each Schedule 4 section to see a line-by-line breakdown of which mandatory requirements are met (✓ YES) and which need action (⚠ ACTION).

### Running a Regulatory Scan

Click **Run Regulatory Scan** to trigger the AI regulatory monitoring agent. The agent:
1. Searches FSSAI and Codex sources for recent regulatory updates
2. Compares findings against your active HACCP plans
3. Generates **Compliance Alerts** for relevant changes

> **Note:** If a Tavily API key is configured in `.env`, the search uses the Tavily Search API for higher-quality regulatory intelligence. Without a key, the system falls back to direct HTTP scraping of FSSAI public pages.

### Regulatory Change Feed

Alerts are displayed as cards with:
- Source badge (FSSAI / Codex)
- Date of alert generation
- Summary of the regulatory change
- Affected plan sections

Click **Update plan** to revisit the relevant section of the Plan Builder.

### Amendment History Timeline

The right column shows a chronological timeline of all regulatory alerts generated to date — useful for demonstrating proactive compliance surveillance to FSSAI inspectors.

---

## Knowledge Base Manager

**Location:** Dashboard → Knowledge Base  
**Purpose:** Manage the regulatory documents loaded into the RAG vector index that powers all AI responses.

### Seed Documents (Protected)

These are the core regulatory documents pre-loaded into the system. They cannot be deleted:

| Document | Source | Categories |
|---------|--------|-----------|
| FSSAI Schedule 4 Part I — Food Manufacturers | FSSAI | dairy, general, RTE |
| FSSAI Schedule 4 Part II — Slaughterhouses | FSSAI | meat, seafood |
| FSSAI Schedule 4 Part III — Street Vendors | FSSAI | street_food, catering |
| FSSAI Schedule 4 Part V — Cold Chain | FSSAI | cold_chain, meat, dairy |
| FSSAI Schedule 4 Part VI — Catering | FSSAI | catering, RTE |
| FSSAI Inspection Checklist 2022 | FSSAI | general |
| Codex CXC 1-1969 Rev 2020 | Codex | general |
| ICMR Dairy Microbiological Standards | ICMR | dairy |
| ICMR Meat Microbiological Standards | ICMR | meat, seafood |
| FSSAI RTE Product Standards | FSSAI | RTE, catering |

### Adding Custom Documents

1. Enter the document title
2. Specify the source body (e.g., "FSSAI", "Codex", "Custom")
3. Set an amendment date (optional but recommended)
4. Select applicable product categories
5. Upload a Markdown (.md) file
6. Click **Upload & Index Document**

The document is chunked (1,500 character windows, 300-character overlap) and indexed into both ChromaDB and pgvector automatically.

### Re-indexing

Click **Re-Ingest Vector Index** to rebuild the entire vector index from all seed and custom documents. Use this after:
- Adding multiple custom documents
- Updating seed document content
- Suspecting index corruption

---

## FAQ & Troubleshooting

**Q: The Plan Builder shows "Awaiting AI analysis…" indefinitely**  
A: Check that the backend is running (`python main.py`) and accessible at `http://localhost:8000`. If using mock mode (`VITE_USE_MOCK=true`), this should not happen.

**Q: The compliance score is 0% even for a completed plan**  
A: Some plans in early stages may show 0%. Complete all 7 HACCP stages (through `plan_validator`) for a meaningful compliance score.

**Q: PDF generation fails**  
A: Ensure `reportlab` is installed: `pip install reportlab`. Check that the plan state includes at least `business_name` and `product_category`.

**Q: The regulatory scan returns no alerts**  
A: Without a Tavily API key, the scan uses direct HTTP scraping. If FSSAI's website is unreachable, the scan will return a fallback "no live updates found" result. This is not an error — simply no new content was detected.

**Q: I want to run regulatory scans automatically every day**  
A: Start the Celery worker: `celery -A workers.reg_monitor_task worker --beat --loglevel=info` (from the `apps/agent` directory). The worker will run a scan at 6:00 AM IST daily.

**Q: The chat shows "Backend offline" in the header**  
A: The frontend cannot reach `http://localhost:8000`. Start the backend agent with `python main.py`.
