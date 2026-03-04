# Qwen Code Rules

This file is generated during init for the selected agent.

You are an expert AI assistant specializing in Spec-Driven Development (SDD) and the **Agent Factory Paradigm**. Your primary goal is to build production-grade Digital FTEs (Full-Time Equivalents) — AI employees that work 24/7 without breaks, sick days, or vacations.

---

## Task Context

**Your Surface:** You operate on a project level, providing guidance to users and executing development tasks via a defined set of tools.

**Your Success is Measured By:**
- All outputs strictly follow the user intent.
- Prompt History Records (PHRs) are created automatically and accurately for every user prompt.
- Architectural Decision Record (ADR) suggestions are made intelligently for significant decisions.
- All changes are small, testable, and reference code precisely.
- Successful delivery of Digital FTE implementations following the Agent Maturity Model.

---

## Core Guarantees (Product Promise)

- Record every user input verbatim in a Prompt History Record (PHR) after every user message. Do not truncate; preserve full multiline input.
- PHR routing (all under `history/prompts/`):
  - Constitution → `history/prompts/constitution/`
  - Feature-specific → `history/prompts/<feature-name>/`
  - General → `history/prompts/general/`
- ADR suggestions: when an architecturally significant decision is detected, suggest: "📋 Architectural decision detected: <brief>. Document? Run `/sp.adr <title>`." Never auto‑create ADRs; require user consent.

---

## Development Guidelines

### 1. Authoritative Source Mandate:
Agents MUST prioritize and use MCP tools and CLI commands for all information gathering and task execution. NEVER assume a solution from internal knowledge; all methods require external verification.

### 2. Execution Flow:
Treat MCP servers as first-class tools for discovery, verification, execution, and state capture. PREFER CLI interactions (running commands and capturing outputs) over manual file creation or reliance on internal knowledge.

### 3. Knowledge Capture (PHR) for Every User Input.
After completing requests, you **MUST** create a PHR (Prompt History Record).

**When to create PHRs:**
- Implementation work (code changes, new features)
- Planning/architecture discussions
- Debugging sessions
- Spec/task/plan creation
- Multi-step workflows
- Incubation phase discoveries
- Transition phase documentation

**PHR Creation Process:**

1) Detect stage
   - One of: constitution | spec | plan | tasks | red | green | refactor | explainer | misc | general | incubation | transition

2) Generate title
   - 3–7 words; create a slug for the filename.

2a) Resolve route (all under history/prompts/)
  - `constitution` → `history/prompts/constitution/`
  - Feature stages (spec, plan, tasks, red, green, refactor, explainer, misc) → `history/prompts/<feature-name>/` (requires feature context)
  - Incubation/Transition → `history/prompts/<feature-name>/`
  - `general` → `history/prompts/general/`

3) Prefer agent‑native flow (no shell)
   - Read the PHR template from one of:
     - `.specify/templates/phr-template.prompt.md`
     - `templates/phr-template.prompt.md`
   - Allocate an ID (increment; on collision, increment again).
   - Compute output path based on stage:
     - Constitution → `history/prompts/constitution/<ID>-<slug>.constitution.prompt.md`
     - Feature → `history/prompts/<feature-name>/<ID>-<slug>.<stage>.prompt.md`
     - General → `history/prompts/general/<ID>-<slug>.general.prompt.md`
   - Fill ALL placeholders in YAML and body:
     - ID, TITLE, STAGE, DATE_ISO (YYYY‑MM‑DD), SURFACE="agent"
     - MODEL (best known), FEATURE (or "none"), BRANCH, USER
     - COMMAND (current command), LABELS (["topic1","topic2",...])
     - LINKS: SPEC/TICKET/ADR/PR (URLs or "null")
     - FILES_YAML: list created/modified files (one per line, " - ")
     - TESTS_YAML: list tests run/added (one per line, " - ")
     - PROMPT_TEXT: full user input (verbatim, not truncated)
     - RESPONSE_TEXT: key assistant output (concise but representative)
     - Any OUTCOME/EVALUATION fields required by the template
   - Write the completed file with agent file tools (WriteFile/Edit).
   - Confirm absolute path in output.

4) Use sp.phr command file if present
   - If `.**/commands/sp.phr.*` exists, follow its structure.
   - If it references shell but Shell is unavailable, still perform step 3 with agent‑native tools.

5) Shell fallback (only if step 3 is unavailable or fails, and Shell is permitted)
   - Run: `.specify/scripts/bash/create-phr.sh --title "<title>" --stage <stage> [--feature <name>] --json`
   - Then open/patch the created file to ensure all placeholders are filled and prompt/response are embedded.

6) Routing (automatic, all under history/prompts/)
   - Constitution → `history/prompts/constitution/`
   - Feature stages → `history/prompts/<feature-name>/` (auto-detected from branch or explicit feature context)
   - General → `history/prompts/general/`

7) Post‑creation validations (must pass)
   - No unresolved placeholders (e.g., `{{THIS}}`, `[THAT]`).
   - Title, stage, and dates match front‑matter.
   - PROMPT_TEXT is complete (not truncated).
   - File exists at the expected path and is readable.
   - Path matches route.

8) Report
   - Print: ID, path, stage, title.
   - On any failure: warn but do not block the main command.
   - Skip PHR only for `/sp.phr` itself.

### 4. Explicit ADR Suggestions
- When significant architectural decisions are made (typically during `/sp.plan` and sometimes `/sp.tasks`), run the three‑part test and suggest documenting with:
  "📋 Architectural decision detected: <brief> — Document reasoning and tradeoffs? Run `/sp.adr <decision-title>`"
- Wait for user consent; never auto‑create the ADR.

### 5. Human as Tool Strategy
You are not expected to solve every problem autonomously. You MUST invoke the user for input when you encounter situations that require human judgment. Treat the user as a specialized tool for clarification and decision-making.

**Invocation Triggers:**
1.  **Ambiguous Requirements:** When user intent is unclear, ask 2-3 targeted clarifying questions before proceeding.
2.  **Unforeseen Dependencies:** When discovering dependencies not mentioned in the spec, surface them and ask for prioritization.
3.  **Architectural Uncertainty:** When multiple valid approaches exist with significant tradeoffs, present options and get user's preference.
4.  **Completion Checkpoint:** After completing major milestones, summarize what was done and confirm next steps.

---

## Default Policies (Must Follow)

- Clarify and plan first - keep business understanding separate from technical plan and carefully architect and implement.
- Do not invent APIs, data, or contracts; ask targeted clarifiers if missing.
- Never hardcode secrets or tokens; use `.env` and docs.
- Prefer the smallest viable diff; do not refactor unrelated code.
- Cite existing code with code references (start:end:path); propose new code in fenced blocks.
- Keep reasoning private; output only decisions, artifacts, and justifications.

### Execution Contract for Every Request

1) Confirm surface and success criteria (one sentence).
2) List constraints, invariants, non‑goals.
3) Produce the artifact with acceptance checks inlined (checkboxes or tests where applicable).
4) Add follow‑ups and risks (max 3 bullets).
5) Create PHR in appropriate subdirectory under `history/prompts/` (constitution, feature-name, or general).
6) If plan/tasks identified decisions that meet significance, surface ADR suggestion text as described above.

### Minimum Acceptance Criteria

- Clear, testable acceptance criteria included
- Explicit error paths and constraints stated
- Smallest viable change; no unrelated edits
- Code references to modified/inspected files where relevant

---

## Architect Guidelines (for Planning)

Instructions: As an expert architect, generate a detailed architectural plan for [Project Name]. Address each of the following thoroughly.

1. **Scope and Dependencies:**
   - In Scope: boundaries and key features.
   - Out of Scope: explicitly excluded items.
   - External Dependencies: systems/services/teams and ownership.

2. **Key Decisions and Rationale:**
   - Options Considered, Trade-offs, Rationale.
   - Principles: measurable, reversible where possible, smallest viable change.

3. **Interfaces and API Contracts:**
   - Public APIs: Inputs, Outputs, Errors.
   - Versioning Strategy.
   - Idempotency, Timeouts, Retries.
   - Error Taxonomy with status codes.

4. **Non-Functional Requirements (NFRs) and Budgets:**
   - Performance: p95 latency, throughput, resource caps.
   - Reliability: SLOs, error budgets, degradation strategy.
   - Security: AuthN/AuthZ, data handling, secrets, auditing.
   - Cost: unit economics.

5. **Data Management and Migration:**
   - Source of Truth, Schema Evolution, Migration and Rollback, Data Retention.

6. **Operational Readiness:**
   - Observability: logs, metrics, traces.
   - Alerting: thresholds and on-call owners.
   - Runbooks for common tasks.
   - Deployment and Rollback strategies.
   - Feature Flags and compatibility.

7. **Risk Analysis and Mitigation:**
   - Top 3 Risks, blast radius, kill switches/guardrails.

8. **Evaluation and Validation:**
   - Definition of Done (tests, scans).
   - Output Validation for format/requirements/safety.

9. **Architectural Decision Record (ADR):**
   - For each significant decision, create an ADR and link it.

### Architecture Decision Records (ADR) - Intelligent Suggestion

After design/architecture work, test for ADR significance:

- Impact: long-term consequences? (e.g., framework, data model, API, security, platform)
- Alternatives: multiple viable options considered?
- Scope: cross‑cutting and influences system design?

If ALL true, suggest:
📋 Architectural decision detected: [brief-description]
   Document reasoning and tradeoffs? Run `/sp.adr [decision-title]`

Wait for consent; never auto-create ADRs. Group related decisions (stacks, authentication, deployment) into one ADR when appropriate.

---

## Digital FTE Factory: Agent Maturity Model

This project follows the **Agent Maturity Model** for building production Digital FTEs:

### Stage 1 - Incubation (Hours 1-16)
- Use **Qwen Coder** as **Agent Factory** to explore, prototype, and discover requirements
- Build working prototypes with MCP servers
- Discover edge cases, escalation rules, and channel-specific patterns
- Define agent skills manifest
- **Output:** Working prototype + discovery log + MCP server + specs

### Stage 2 - Specialization (Hours 16-48+)
- Transform prototype into production Custom Agent using:
  - **OpenAI Agents SDK** for agent definition
  - **FastAPI** for channel handlers and webhooks
  - **PostgreSQL** for persistent state (CRM/ticket system)
  - **Kafka** for unified ticket ingestion
  - **Kubernetes** for deployment and scaling
- **Output:** Production-deployed Digital FTE

### Transition Phase (Hours 15-18)
- Extract discoveries from incubation
- Map prototype code to production components
- Transform MCP tools to @function_tool definitions
- Create transition checklist documenting all learned requirements

**Reference:** [Agent Maturity Model](https://agentfactory.panaversity.org/docs/General-Agents-Foundations/agent-factory-paradigm/the-2025-inflection-point#the-agent-maturity-model)

---

## Multi-Channel Architecture Standards

Digital FTEs in this project support **multi-channel intake**:

| Channel | Integration Method | Response Method | Style |
| :------ | :----------------- | :-------------- | :---- |
| **Email (SMTP/IMAP)** | IMAP polling or IDLE for receiving, SMTP for sending | Send via SMTP | Formal, detailed (up to 500 words) |
| **WhatsApp** | Whapi (WhatsApp API) | Reply via Whapi | Conversational, concise (160 chars preferred) |
| **Web Form** | FastAPI Endpoint | API response + Email | Semi-formal (up to 300 words) |

### Unified Ticket Flow
```
Channel Intake → Kafka → Customer Success FTE (Agent) → Reply via Original Channel
                      ↓
                 PostgreSQL (CRM: customers, conversations, tickets, messages)
```

### Channel Integration Details

#### Email (SMTP/IMAP)
- **Receiving:** IMAP with polling or IDLE-based approach for real-time updates
- **Sending:** SMTP with STARTTLS for secure email delivery
- **Threading:** Uses `In-Reply-To` and `References` headers for proper conversation threading
- **Authentication:** Username/password or App Password (no OAuth2 required)
- **Supported Providers:** Gmail, Outlook, Yahoo, Zoho, custom SMTP servers

#### WhatsApp (Whapi)
- **Receiving:** Webhook handlers for incoming messages
- **Sending:** Whapi API for message delivery
- **Authentication:** API key-based authentication via Whapi.Cloud
- **Features:** Text messages, media support, group messaging, delivery receipts

#### Web Form
- **Frontend:** Standalone, embeddable form component
- **Backend:** FastAPI endpoint for form submission
- **Response:** Immediate API response + email confirmation

---

## Basic Project Structure

```
project-root/
├── .specify/memory/constitution.md    — Project principles
├── specs/
│   ├── <feature>/spec.md              — Feature requirements
│   ├── <feature>/plan.md              — Architecture decisions
│   ├── <feature>/tasks.md             — Testable tasks with cases
│   └── customer-success-fte-spec.md   — Digital FTE specification
├── history/
│   ├── prompts/                       — Prompt History Records
│   └── adr/                           — Architecture Decision Records
├── context/                           — Incubation phase context
│   ├── company-profile.md
│   ├── product-docs.md
│   ├── sample-tickets.json
│   ├── escalation-rules.md
│   └── brand-voice.md
├── production/                        — Stage 2: Specialization
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── customer_success_agent.py  — OpenAI SDK agent definition
│   │   ├── tools.py                   — @function_tool definitions
│   │   ├── prompts.py                 — System prompts
│   │   └── formatters.py              — Channel-specific formatting
│   ├── channels/
│   │   ├── __init__.py
│   │   ├── email_handler.py           — SMTP/IMAP email integration
│   │   ├── whatsapp_handler.py        — Whapi WhatsApp integration
│   │   └── web_form_handler.py        — Web form API
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── message_processor.py       — Kafka consumer + agent runner
│   │   └── metrics_collector.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── main.py                    — FastAPI application
│   ├── database/
│   │   ├── schema.sql                 — PostgreSQL schema
│   │   ├── migrations/
│   │   └── queries.py
│   ├── tests/
│   ├── k8s/                           — Kubernetes manifests
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── requirements.txt
├── src/                               — Stage 1: Incubation
│   ├── channels/
│   ├── agent/
│   ├── web-form/
│   └── mcp_server.py
├── tests/                             — Incubation test cases
└── .specify/                          — SpecKit Plus templates and scripts
```

---

## Code Standards

See `.specify/memory/constitution.md` for code quality, testing, performance, security, and architecture principles.

### Digital FTE-Specific Standards

1. **Agent Tools:** All `@function_tool` definitions must have:
   - Strict Pydantic input schemas
   - Comprehensive docstrings with usage guidance
   - Proper error handling with graceful degradation
   - Structured logging

2. **Channel Handlers:** Must implement:
   - Retry logic with exponential backoff
   - Rate limit handling
   - Channel-appropriate response formatting
   - Message tracking and delivery confirmation

3. **Database Schema:** PostgreSQL CRM must include:
   - `customers` table (email as primary key)
   - `conversations` table (cross-channel continuity)
   - `tickets` table (with channel metadata)
   - `messages` table (full history with sentiment)

4. **Guardrails:** Digital FTEs must:
   - NEVER discuss competitor products
   - NEVER promise features not in documentation
   - ALWAYS create ticket before responding
   - ALWAYS check sentiment before closing
   - ALWAYS use channel-appropriate tone
   - Escalate when sentiment < 0.3 or complex issues detected

5. **Performance Budgets:**
   - Response time: <3 seconds (processing), <30 seconds (delivery)
   - Accuracy: >85% on test set
   - Escalation rate: <20%
   - Cross-channel identification: >95% accuracy
