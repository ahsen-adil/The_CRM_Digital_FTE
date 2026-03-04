<!--
SYNC IMPACT REPORT
==================
Version change: 0.0.0 → 1.0.0 (Initial constitution for CRM Digital FTE Factory)
Added sections:
  - All 7 Core Principles (Incubation-First, Multi-Channel Architecture, Production-Grade Tooling, etc.)
  - Agent Maturity Model Compliance
  - Security & Secrets Management
  - Development Workflow & Quality Gates
Removed sections: None (initial version)
Templates requiring updates:
  - .specify/templates/plan-template.md ✅ aligned (Constitution Check section references principles)
  - .specify/templates/spec-template.md ✅ aligned (guardrails section added)
  - .specify/templates/tasks-template.md ✅ aligned (phase structure matches incubation→production workflow)
Follow-up TODOs: None
-->

# CRM Digital FTE Factory Constitution

## Core Principles

### I. Agent Maturity Model Compliance
All Digital FTE development MUST follow the two-stage Agent Maturity Model:

**Stage 1 - Incubation (Hours 1-16):**
- Use Qwen Coder as Agent Factory to explore, prototype, and discover requirements
- Build working prototypes with MCP servers exposing 5+ tools
- Discover edge cases, escalation rules, and channel-specific patterns through testing
- Define agent skills manifest with clear input/output contracts
- Output: Working prototype + discovery log + MCP server + specs

**Stage 2 - Specialization (Hours 16-48+):**
- Transform prototype into production Custom Agent using OpenAI Agents SDK
- Implement proper error handling, structured logging, and database persistence
- Deploy with Kubernetes orchestration and Kafka event streaming
- Output: Production-deployed Digital FTE with monitoring and alerting

**Transition Phase (Hours 15-18):** Mandatory documentation of discovered requirements, working prompts, edge cases, and performance baselines before production implementation begins.

### II. Multi-Channel Architecture
Every Digital FTE MUST support multi-channel intake with unified processing:

**Required Channels:**
- **Email (SMTP/IMAP):** IMAP polling or IDLE for receiving, SMTP with STARTTLS for sending
- **WhatsApp (Whapi):** Webhook handlers for incoming, Whapi API for outgoing
- **Web Form:** FastAPI endpoint with standalone embeddable UI component

**Architecture Requirements:**
- All channels MUST route through Kafka for unified ticket ingestion
- Cross-channel conversation continuity MUST be maintained (customer identified by email as primary key)
- Channel-appropriate response formatting MUST be applied (email: formal/detailed, WhatsApp: conversational/concise, web: semi-formal)
- Original channel MUST be preserved in ticket metadata for response routing

### III. Incubation-First Development
All features MUST start with exploratory prototyping before production implementation:

- **Discovery-driven:** Qwen Coder MUST analyze sample tickets, identify patterns, and surface channel-specific behaviors
- **Iterative refinement:** Prototypes MUST be tested with real scenarios and iterated based on failures
- **MCP exposure:** Capabilities MUST be exposed as MCP tools before OpenAI SDK conversion
- **Skills manifest:** Agent capabilities MUST be formalized as reusable skill definitions

**Prohibited:** Skipping incubation phase or writing production code without discovered requirements.

### IV. Production-Grade Tooling
All `@function_tool` definitions MUST meet production standards:

- **Strict schemas:** Pydantic BaseModel with typed fields and validation rules
- **Comprehensive docstrings:** Usage guidance for LLM consumption with Args/Returns sections
- **Error handling:** Try/catch with graceful degradation and fallback responses
- **Structured logging:** All operations logged with correlation IDs for debugging
- **Database integration:** PostgreSQL with connection pooling, not in-memory storage

**Tool categories:** Knowledge retrieval, ticket management, customer history, escalation, response delivery.

### V. Guardrails & Escalation
Digital FTEs MUST enforce strict guardrails with automatic escalation:

**NEVER:**
- Discuss competitor products
- Promise features not in documentation
- Respond without creating a ticket first
- Close tickets without sentiment check
- Use inappropriate tone for channel

**ALWAYS escalate when:**
- Customer sentiment < 0.3 (angry/frustrated)
- Pricing negotiations or refund requests
- Legal/compliance questions
- Complex issues beyond documented scope
- Knowledge base returns no relevant results

**Escalation MUST include:** Full conversation context, sentiment trend, attempted resolutions, and reason code.

### VI. Performance Budgets
All Digital FTEs MUST meet measurable performance targets:

- **Response time:** <3 seconds processing, <30 seconds delivery
- **Accuracy:** >85% on test set of 50+ sample tickets
- **Escalation rate:** <20% of total tickets
- **Cross-channel identification:** >95% accuracy in customer matching
- **Availability:** 24/7 operation with <1% downtime

**Monitoring:** All metrics MUST be tracked via Kafka events and exposed via Prometheus-compatible endpoints.

### VII. Database-First State Management
All customer interactions MUST be persisted in PostgreSQL with proper schema:

**Required Tables:**
- `customers` (email as primary key, unified identity across channels)
- `conversations` (cross-channel continuity with thread tracking)
- `tickets` (with channel metadata, status, priority, escalation flags)
- `messages` (full history with sentiment scores, topics, resolution status)

**Schema Evolution:** All changes MUST use migration files with rollback support. No direct schema modifications in production.

## Security & Secrets Management

**Credentials:**
- API keys, passwords, and tokens MUST be stored in `.env` files
- `.env` MUST be in `.gitignore` - never commit secrets
- Use App Passwords for Gmail/SMTP instead of OAuth2 where possible
- Whapi API keys MUST be rotated every 90 days

**Data Handling:**
- Customer PII MUST be encrypted at rest
- Message content MUST be redacted in logs
- Access to production database requires approval and audit trail

**Authentication:**
- SMTP/IMAP: Username/password or App Password (no OAuth2 required)
- Whapi: API key-based authentication via Whapi.Cloud
- FastAPI endpoints: API key or JWT token validation

## Development Workflow & Quality Gates

**Phase 0 - Incubation:**
- [ ] Context files created (company-profile.md, sample-tickets.json, escalation-rules.md, brand-voice.md)
- [ ] Qwen Coder exploration completed with discovery log
- [ ] MCP server with 5+ tools implemented and tested
- [ ] Agent skills manifest defined
- [ ] Performance baseline established

**Phase 1 - Transition:**
- [ ] Transition checklist completed (specs/transition-checklist.md)
- [ ] Working prompts extracted and documented
- [ ] Edge cases catalogued with test cases
- [ ] Code mapping from incubation to production completed

**Phase 2 - Specialization:**
- [ ] OpenAI Agents SDK agent implemented with @function_tool decorators
- [ ] Channel handlers (email_handler.py, whatsapp_handler.py, web_form_handler.py) with retry logic
- [ ] PostgreSQL schema with migrations
- [ ] Kafka consumers/workers for async processing
- [ ] Kubernetes manifests for deployment
- [ ] pytest test suite with >80% coverage

**Phase 3 - Operational Readiness:**
- [ ] Structured logging configured
- [ ] Metrics collection and alerting thresholds defined
- [ ] Runbooks for common tasks (escalation review, sentiment analysis, ticket cleanup)
- [ ] Deployment and rollback procedures documented

**Quality Gates:**
- All PRs MUST verify constitution compliance
- Constitution Check in plan.md MUST pass before Phase 2 implementation
- Performance budgets MUST be validated against test set before deployment

## Governance

This constitution supersedes all other development practices for the CRM Digital FTE Factory project.

**Amendment Process:**
- Changes require documentation of rationale and impact analysis
- Backward-incompatible changes (principle removals, redefinitions) require MAJOR version bump
- New principles or sections require MINOR version bump
- Clarifications and typo fixes require PATCH version bump

**Compliance Review:**
- All feature specs MUST include Constitution Check section
- Plan templates MUST reference applicable principles
- Task lists MUST include quality gate checkpoints

**Versioning Policy:** Semantic versioning (MAJOR.MINOR.PATCH) aligned with constitution changes.

---

**Version**: 1.0.0 | **Ratified**: 2026-02-27 | **Last Amended**: 2026-02-27
