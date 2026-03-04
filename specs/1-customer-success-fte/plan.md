# Implementation Plan: Customer Success Digital FTE

**Branch**: `1-customer-success-fte` | **Date**: 2026-02-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification for Customer Success AI agent handling multi-channel customer support inquiries

## Summary

Build a Customer Success Digital FTE that handles customer inquiries 24/7 across three channels (Email via SMTP/IMAP, WhatsApp via Whapi, Web Form via FastAPI). The system will automatically respond to routine questions using product documentation, escalate complex issues to human agents, maintain conversation continuity across channels, and track all interactions in PostgreSQL. Implementation follows the Agent Maturity Model: Stage 1 Incubation (Qwen Coder prototyping with MCP server) → Transition (documentation) → Stage 2 Specialization (OpenAI Agents SDK production deployment).

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: OpenAI Agents SDK, FastAPI, asyncpg (PostgreSQL), python-dotenv, smtplib/imaplib (built-in), whapi-sdk
**Storage**: PostgreSQL 15+ with pgvector for semantic search
**Testing**: pytest with async support, pytest-asyncio
**Target Platform**: Linux server (Docker containers on Kubernetes)
**Project Type**: Single project with modular structure (agent, channels, workers, api)
**Performance Goals**: <3 seconds processing time, <30 seconds delivery time, 85%+ accuracy on test set
**Constraints**: <20% escalation rate, >95% cross-channel identification accuracy, 24/7 operation with <1% downtime
**Scale/Scope**: Support 10,000+ tickets/month, 50+ sample tickets for testing, 3 communication channels

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Compliance Status | Notes |
|-----------------------|-------------------|-------|
| **I. Agent Maturity Model Compliance** | ✅ PASS | Plan follows two-stage approach: Incubation (MCP server prototyping) → Specialization (OpenAI SDK production) |
| **II. Multi-Channel Architecture** | ✅ PASS | All three required channels included: SMTP/IMAP email, Whapi WhatsApp, FastAPI web form |
| **III. Incubation-First Development** | ✅ PASS | Phase 0-1 dedicated to incubation with Qwen Coder, MCP server, discovery log |
| **IV. Production-Grade Tooling** | ✅ PASS | Tools use Pydantic schemas, error handling, structured logging, PostgreSQL |
| **V. Guardrails & Escalation** | ✅ PASS | Escalation rules implemented: sentiment < 0.3, pricing/refund/legal topics |
| **VI. Performance Budgets** | ✅ PASS | Targets match constitution: <3s processing, <30s delivery, >85% accuracy, <20% escalation |
| **VII. Database-First State Management** | ✅ PASS | PostgreSQL schema with customers, conversations, tickets, messages tables |

**GATE RESULT**: ✅ PASS - All constitution principles satisfied. Proceeding to Phase 0 research.

## Project Structure

### Documentation (this feature)

```text
specs/1-customer-success-fte/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
src/                               # Stage 1: Incubation
├── channels/
│   ├── email_handler.py           # SMTP/IMAP email integration
│   ├── whatsapp_handler.py        # Whapi WhatsApp integration
│   └── web_form_handler.py        # Web form API
├── agent/
│   ├── core_agent.py              # Core agent logic
│   └── mcp_server.py              # MCP server with tools
└── web-form/                      # Standalone embeddable form

production/                        # Stage 2: Specialization
├── agent/
│   ├── __init__.py
│   ├── customer_success_agent.py  # OpenAI SDK agent definition
│   ├── tools.py                   # @function_tool definitions
│   ├── prompts.py                 # System prompts
│   └── formatters.py              # Channel-specific formatting
├── channels/
│   ├── __init__.py
│   ├── email_handler.py           # SMTP/IMAP with retry logic
│   ├── whatsapp_handler.py        # Whapi webhook handlers
│   └── web_form_handler.py        # Web form API
├── workers/
│   ├── __init__.py
│   ├── message_processor.py       # Kafka consumer + agent runner
│   └── metrics_collector.py       # Background metrics
├── api/
│   ├── __init__.py
│   └── main.py                    # FastAPI application
├── database/
│   ├── schema.sql                 # PostgreSQL schema
│   ├── migrations/                # Database migrations
│   └── queries.py                 # Database access functions
├── tests/
│   ├── test_agent.py
│   ├── test_channels.py
│   └── test_e2e.py
├── k8s/                           # Kubernetes manifests
├── Dockerfile
├── docker-compose.yml             # Local development
└── requirements.txt

context/                           # Incubation phase context
├── company-profile.md
├── product-docs.md
├── sample-tickets.json
├── escalation-rules.md
└── brand-voice.md

tests/                             # Incubation test cases
```

**Structure Decision**: Single project with modular structure for Stage 1 (incubation), expanding to full production structure for Stage 2 (specialization). This aligns with constitution's Agent Maturity Model and allows iterative development from prototype to production.

## Complexity Tracking

No constitution violations. All principles satisfied with standard architecture.

---

## Phase 0: Research & Technology Decisions

### Research Tasks

1. **SMTP/IMAP Email Integration**: Research best practices for Python smtplib/imaplib with Gmail App Passwords
2. **Whapi WhatsApp Integration**: Research Whapi.Cloud webhook handling and message formatting
3. **OpenAI Agents SDK**: Research @function_tool decorators, agent workflows, and handoff patterns
4. **PostgreSQL with pgvector**: Research vector similarity search for knowledge base semantic search
5. **Kafka Event Streaming**: Research Kafka consumer patterns for async message processing
6. **FastAPI Webhooks**: Research webhook handler patterns for WhatsApp and web form submissions
7. **Sentiment Analysis**: Research sentiment analysis libraries and thresholds for escalation triggers
8. **Kubernetes Deployment**: Research K8s manifests for Python async workers and FastAPI services

---

## Phase 1: Design & Contracts

### Data Model Design

**Entities from spec:**
- Customer (email primary key, cross-channel identity)
- Ticket (support inquiry tracking)
- Conversation (cross-channel thread continuity)
- Message (individual message with sentiment)
- Escalation (human handoff tracking)

### API Contracts

**Endpoints from functional requirements:**
- POST /api/v1/tickets - Create ticket from any channel
- GET /api/v1/tickets/{id} - Get ticket status
- GET /api/v1/customers/{email}/history - Get customer conversation history
- POST /api/v1/webhooks/whatsapp - WhatsApp webhook handler
- POST /api/v1/webhooks/email - Email webhook handler (if using polling alternative)
- POST /api/v1/support - Web form submission
- GET /api/v1/metrics - Performance metrics (for monitoring)

### Agent Context Update

Run `.specify/scripts/powershell/update-agent-context.ps1 -AgentType qwen` to add:
- OpenAI Agents SDK patterns
- SMTP/IMAP email integration
- Whapi WhatsApp integration
- PostgreSQL with pgvector
- Kafka consumer patterns

---

## Next Steps

1. Complete Phase 0 research tasks → `research.md`
2. Generate data model → `data-model.md`
3. Generate API contracts → `contracts/*.yaml`
4. Create quickstart guide → `quickstart.md`
5. Update agent context file
6. Re-evaluate Constitution Check post-design
7. Proceed to `/sp.tasks` for task breakdown

---

**Artifacts to Generate:**
- `research.md` (Phase 0)
- `data-model.md` (Phase 1)
- `contracts/` directory with OpenAPI schemas (Phase 1)
- `quickstart.md` (Phase 1)
- Agent context update (Phase 1)
