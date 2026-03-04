---

description: "Task list for Customer Success Digital FTE implementation"
---

# Tasks: Customer Success Digital FTE

**Input**: Design documents from `/specs/1-customer-success-fte/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Tests are OPTIONAL and NOT included in this task list. Add them separately if TDD approach is requested.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., [US1], [US2], [US3])
- Include exact file paths in descriptions

## Path Conventions

- **Stage 1 (Incubation)**: `src/` at repository root
- **Stage 2 (Production)**: `production/` at repository root
- **Context files**: `context/` at repository root
- **Tests**: `tests/` for incubation, `production/tests/` for production

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (src/, production/, context/, tests/)
- [X] T002 Initialize Python 3.11+ project with requirements.txt dependencies
- [X] T003 [P] Configure linting (flake8, black) and formatting tools (.gitignore, .dockerignore)
- [X] T004 [P] Create .env template and .gitignore with sensitive files (.env.example, .gitignore, .dockerignore)
- [X] T005 [P] Setup Docker Compose for local development (PostgreSQL, Kafka, Zookeeper)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Create PostgreSQL schema in production/database/schema.sql with all tables (customers, conversations, tickets, messages, escalations, knowledge_base)
- [X] T007 [P] Create database migrations framework in production/database/migrations/
- [X] T008 [P] Implement database connection pool in production/database/queries.py using asyncpg
- [X] T009 Setup environment configuration management in production/config.py (load .env variables)
- [X] T010 [P] Configure structured logging infrastructure in production/utils/logging.py
- [X] T011 [P] Create base exception classes in production/utils/exceptions.py
- [X] T012 Setup Kafka configuration in production/utils/kafka.py (bootstrap servers, topic names, producer/consumer)
- [X] T013 Create shared Pydantic models in production/schemas.py for request/response validation

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Submit Support Inquiry via Email (Priority: P1) 🎯 MVP

**Goal**: Enable customers to send support inquiries via email and receive intelligent automated responses within 30 seconds

**Independent Test**: Send an email to support@company.com and verify receipt of automated, contextually relevant response within 30 seconds

### Implementation for User Story 1

- [X] T014 [P] [US1] Create Customer model in production/database/repository.py (email primary key, phone, name, total_tickets, average_sentiment)
- [X] T015 [P] [US1] Create Ticket model in production/database/repository.py (ticket_number, channel, status, priority, sentiment_score)
- [X] T016 [P] [US1] Create Conversation model in production/database/repository.py (customer_id, topic, status, channel_history, resolution_status)
- [X] T017 [P] [US1] Create Message model in production/database/repository.py (message_id, conversation_id, channel, direction, content, sentiment_score)
- [X] T018 [US1] Implement email receiving with IMAP polling in src/channels/email_handler.py (imaplib, fetch UNSEEN emails)
- [X] T019 [US1] Implement email parsing in src/channels/email_handler.py (extract subject, from, body, headers, threading)
- [X] T020 [US1] Implement email sending with SMTP in src/channels/email_handler.py (smtplib, STARTTLS, In-Reply-To, References headers)
- [X] T021 [US1] Create ticket creation logic in src/agent/core_agent.py (generate ticket_number, set channel='email')
- [X] T022 [US1] Implement knowledge base search function in src/agent/core_agent.py (search product docs for relevant info)
- [X] T023 [US1] Create email response formatter in src/agent/core_agent.py (formal tone, up to 500 words, greeting/signature)
- [X] T024 [US1] Implement email threading detection in src/channels/email_handler.py (parse In-Reply-To, References headers)
- [X] T025 [US1] Add email-specific error handling and retry logic in src/channels/email_handler.py
- [X] T026 [US1] Create context/company-profile.md with company details
- [X] T027 [US1] Create context/product-docs.md with product documentation for knowledge base
- [X] T028 [US1] Create context/sample-tickets.json with 50+ sample email inquiries
- [X] T029 [US1] Create context/escalation-rules.md with escalation triggers and assignment rules
- [X] T030 [US1] Create context/brand-voice.md with email response templates and tone guidelines
- [X] T031 [US1] Build MCP server in src/agent/mcp_server.py with tools: search_knowledge_base, create_ticket, get_customer_history, send_response
- [ ] T032 [US1] Test email end-to-end flow in tests/test_email_e2e.py (send test email, verify response)

**Checkpoint**: At this point, User Story 1 should be fully functional - customers can email support and receive automated responses

---

## Phase 4: User Story 2 - Submit Support Inquiry via WhatsApp (Priority: P1)

**Goal**: Enable customers to send support inquiries via WhatsApp and receive concise conversational responses within 30 seconds

**Independent Test**: Send a WhatsApp message to the business number and verify receipt of intelligent, concise response within 30 seconds

### Implementation for User Story 2

- [ ] T033 [P] [US2] Extend Ticket model in production/database/queries.py to support channel='whatsapp'
- [ ] T034 [P] [US2] Extend Message model in production/database/queries.py to support WhatsApp message IDs
- [ ] T035 [US2] Implement WhatsApp webhook handler in production/channels/whatsapp_handler.py (Whapi.Cloud webhook endpoint)
- [ ] T036 [US2] Implement WhatsApp message receiving in production/channels/whatsapp_handler.py (parse incoming webhook payload)
- [ ] T037 [US2] Implement WhatsApp message sending in production/channels/whatsapp_handler.py (Whapi API, text messages)
- [ ] T038 [US2] Create WhatsApp response formatter in production/channels/whatsapp_handler.py (conversational tone, concise, 160 chars preferred, emojis)
- [ ] T039 [US2] Implement WhatsApp-specific error handling and retry logic in production/channels/whatsapp_handler.py
- [ ] T040 [US2] Add WhatsApp phone number to Customer model in production/database/queries.py (E.164 format)
- [ ] T041 [US2] Create sample WhatsApp conversations in context/sample-tickets.json (chat-style messages)
- [ ] T042 [US2] Update brand-voice.md with WhatsApp response templates (conversational, concise)
- [ ] T043 [US2] Extend MCP server with WhatsApp-specific tools in src/agent/mcp_server.py
- [ ] T044 [US2] Test WhatsApp end-to-end flow in tests/test_whatsapp_e2e.py (send test message via Whapi, verify response)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - email and WhatsApp channels operational

---

## Phase 5: User Story 3 - Submit Support Inquiry via Web Form (Priority: P2)

**Goal**: Provide standalone embeddable web form for customers to submit support inquiries from the website

**Independent Test**: Fill out and submit the web support form, verify immediate on-screen confirmation and email acknowledgment with ticket ID

### Implementation for User Story 3

- [ ] T045 [P] [US3] Create WebFormRequest Pydantic model in production/schemas.py (email, name, subject, message, priority, category)
- [ ] T046 [P] [US3] Create WebFormResponse Pydantic model in production/schemas.py (success, ticket_number, message, estimated_response_time)
- [ ] T047 [US3] Implement FastAPI endpoint POST /api/v1/support in production/api/main.py
- [ ] T048 [US3] Create web form HTML/CSS component in src/web-form/support-form.html (standalone, embeddable)
- [ ] T049 [US3] Implement form validation in production/api/main.py (email format, required fields, message length)
- [ ] T050 [US3] Create ticket creation from web form in production/api/main.py (channel='web_form')
- [ ] T051 [US3] Implement email confirmation sending in production/api/main.py (send ticket ID to customer email)
- [ ] T052 [US3] Add CORS middleware to FastAPI in production/api/main.py (allow embedding on company website)
- [ ] T053 [US3] Create web form success page in src/web-form/success.html (confirmation message, ticket number display)
- [ ] T054 [US3] Test web form end-to-end in tests/test_webform_e2e.py (submit form, verify ticket creation, check confirmation email)

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently - all three channels operational

---

## Phase 6: User Story 4 - Cross-Channel Conversation Continuity (Priority: P2)

**Goal**: Maintain conversation context when customers switch channels (e.g., start with WhatsApp, follow up via email)

**Independent Test**: Customer who starts conversation on WhatsApp and follows up via email receives response that acknowledges previous WhatsApp conversation without re-explanation

### Implementation for User Story 4

- [ ] T055 [P] [US4] Extend Conversation model in production/database/queries.py (channel_history array, sentiment_trend JSONB)
- [ ] T056 [P] [US4] Create customer identification service in production/services/customer_identifier.py (match by email, phone number)
- [ ] T057 [US4] Implement cross-channel customer lookup in production/services/customer_identifier.py (find customer by email across channels)
- [ ] T058 [US4] Create conversation continuity logic in production/agents/core_agent.py (link new message to existing conversation)
- [ ] T059 [US4] Implement channel history tracking in production/database/queries.py (append channel to channel_history array)
- [ ] T060 [US4] Create conversation context builder in production/agents/core_agent.py (gather all messages from conversation across channels)
- [ ] T061 [US4] Implement sentiment trend tracking in production/services/sentiment_analyzer.py (track sentiment over conversation lifetime)
- [ ] T062 [US4] Update email handler to use conversation continuity in production/channels/email_handler.py (check for existing conversation)
- [ ] T063 [US4] Update WhatsApp handler to use conversation continuity in production/channels/whatsapp_handler.py (check for existing conversation)
- [ ] T064 [US4] Test cross-channel continuity in tests/test_cross_channel_e2e.py (start WhatsApp, follow up email, verify context maintained)

**Checkpoint**: At this point, User Stories 1-4 should all work - customers can switch channels seamlessly

---

## Phase 7: User Story 5 - Automatic Escalation to Human Agent (Priority: P3)

**Goal**: Automatically escalate to human agents when sentiment is negative or issue is outside AI scope (pricing, refunds, legal)

**Independent Test**: Send message with negative sentiment or escalation keywords, verify system escalates to human with full context

### Implementation for User Story 5

- [ ] T065 [P] [US5] Create Escalation model in production/database/queries.py (escalation_number, reason_code, assigned_team, priority, status)
- [ ] T066 [P] [US5] Create EscalationRequest Pydantic model in production/schemas.py (ticket_id, reason_code, reason_details)
- [ ] T067 [US5] Implement sentiment analysis service in production/services/sentiment_analyzer.py (Hugging Face transformers, sentiment score -1.0 to 1.0)
- [ ] T068 [US5] Create escalation decision logic in production/agents/core_agent.py (sentiment < 0.3, pricing/refund/legal keywords)
- [ ] T069 [US5] Implement escalation creation in production/database/queries.py (generate escalation_number, set reason_code)
- [ ] T070 [US5] Create escalation notification service in production/services/escalation_notifier.py (email assigned team, include conversation context)
- [ ] T071 [US5] Implement escalation API endpoint POST /api/v1/escalations in production/api/main.py
- [ ] T072 [US5] Create escalation reason code enum in production/schemas.py (negative_sentiment, pricing_request, refund_request, legal_compliance, complex_issue, knowledge_gap, customer_request)
- [ ] T073 [US5] Add escalation detection to email handler in production/channels/email_handler.py (check sentiment before responding)
- [ ] T074 [US5] Add escalation detection to WhatsApp handler in production/channels/whatsapp_handler.py (check sentiment before responding)
- [ ] T075 [US5] Create escalation response template in production/agents/prompts.py (acknowledge escalation, provide SLA)
- [ ] T076 [US5] Test escalation end-to-end in tests/test_escalation_e2e.py (send angry message, verify escalation created, notification sent)

**Checkpoint**: At this point, all 5 user stories are complete - full Customer Success Digital FTE operational

---

## Phase 8: Stage 2 Specialization (Production Deployment)

**Goal**: Transform incubation prototype into production-grade Custom Agent using OpenAI Agents SDK

### Implementation for Phase 8

- [ ] T077 [P] Create OpenAI Agents SDK agent definition in production/agent/customer_success_agent.py
- [ ] T078 [P] Convert MCP tools to @function_tool decorators in production/agent/tools.py (search_knowledge_base, create_ticket, get_customer_history, escalate_to_human, send_response)
- [ ] T079 [P] Create Pydantic input schemas for all tools in production/agent/tools.py (KnowledgeSearchInput, CreateTicketInput, etc.)
- [ ] T080 [P] Extract system prompts to production/agent/prompts.py (formalized with explicit constraints)
- [ ] T081 [P] Create channel-specific formatters in production/agent/formatters.py (email, whatsapp, web_form)
- [ ] T082 [P] Implement Kafka consumer in production/workers/message_processor.py (consume tickets.incoming topic)
- [ ] T083 [P] Implement Kafka producer integration in production/agents/customer_success_agent.py (publish to tickets.responses)
- [ ] T084 [P] Create FastAPI application in production/api/main.py with all endpoints from OpenAPI spec
- [ ] T085 [P] Implement webhook signature verification in production/api/main.py (WhatsApp webhook security)
- [ ] T086 [P] Create Kubernetes manifests in production/k8s/ (deployments, services, ConfigMaps)
- [ ] T087 [P] Create Dockerfile in production/Dockerfile (multi-stage build, Python 3.11)
- [ ] T088 [P] Implement metrics collection in production/workers/metrics_collector.py (response time, escalation rate, accuracy)
- [ ] T089 [P] Create Prometheus metrics endpoint GET /api/v1/metrics in production/api/main.py
- [ ] T090 [P] Write production test suite in production/tests/ (test_agent.py, test_channels.py, test_e2e.py)

**Checkpoint**: Production-ready Customer Success Digital FTE deployed on Kubernetes

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final polish, documentation, and operational readiness

- [ ] T091 Create comprehensive README.md with setup instructions and architecture overview
- [ ] T092 [P] Create API documentation with OpenAPI UI (Swagger/ReDoc)
- [ ] T093 [P] Setup monitoring dashboards (Grafana for metrics visualization)
- [ ] T094 [P] Create alerting rules (response time > 30s, escalation rate > 20%, downtime > 1%)
- [ ] T095 [P] Write runbooks for common tasks (escalation review, sentiment analysis tuning, ticket cleanup)
- [ ] T096 [P] Create deployment and rollback procedures documentation
- [ ] T097 [P] Setup CI/CD pipeline (GitHub Actions or GitLab CI)
- [ ] T098 [P] Configure staging environment for testing before production
- [ ] T099 [P] Perform load testing (verify <3s processing at 100 concurrent users)
- [ ] T100 [P] Perform security audit (API key validation, SQL injection prevention, XSS protection)

---

## Dependency Graph

**User Story Completion Order** (for incremental MVP delivery):

```
Phase 1-2: Setup & Foundation (T001-T013)
              ↓
Phase 3: US1 - Email Support (T014-T032) ← MVP
              ↓
Phase 4: US2 - WhatsApp Support (T033-T044)
              ↓
Phase 5: US3 - Web Form (T045-T054)
              ↓
Phase 6: US4 - Cross-Channel Continuity (T055-T064)
              ↓
Phase 7: US5 - Escalation (T065-T076)
              ↓
Phase 8: Production Deployment (T077-T090)
              ↓
Phase 9: Polish (T091-T100)
```

---

## Parallel Execution Examples

**Within Phase 1-2 (Setup & Foundation)**:
- T003 (linting), T004 (.env), T005 (Docker) can run in parallel
- T006 (schema), T007 (migrations), T010 (logging) can run in parallel

**Within Phase 3 (US1 - Email)**:
- T014-T017 (models) can run in parallel
- T026-T030 (context files) can run in parallel

**Within Phase 4 (US2 - WhatsApp)**:
- T033-T034 (model extensions) can run in parallel
- T035 (webhook), T036 (receiving), T037 (sending) have dependencies - run sequentially

**Within Phase 8 (Production)**:
- T077-T081 (agent components) can run in parallel
- T082 (Kafka consumer), T083 (Kafka producer) can run in parallel
- T086 (K8s), T087 (Dockerfile) can run in parallel

---

## Implementation Strategy

**MVP Scope** (minimum viable product):
- Phase 1-2: Setup & Foundation (T001-T013)
- Phase 3: Email Support only (T014-T032)
- **Result**: Customers can email support and receive automated responses

**Increment 2** (add WhatsApp):
- Phase 4: WhatsApp Support (T033-T044)
- **Result**: Customers can use email OR WhatsApp

**Increment 3** (add Web Form):
- Phase 5: Web Form (T045-T054)
- **Result**: All three channels operational

**Increment 4** (cross-channel continuity):
- Phase 6: Cross-Channel Continuity (T055-T064)
- **Result**: Seamless experience when switching channels

**Increment 5** (escalation):
- Phase 7: Automatic Escalation (T065-T076)
- **Result**: Full Customer Success Digital FTE with human handoff

**Production Deployment**:
- Phase 8: Specialization (T077-T090)
- **Result**: Production-grade deployment on Kubernetes

**Operational Readiness**:
- Phase 9: Polish (T091-T100)
- **Result**: Fully operational with monitoring, alerting, documentation

---

## Task Summary

| Phase | Description | Task Count |
| :---- | :---------- | :--------- |
| Phase 1 | Setup | 5 tasks |
| Phase 2 | Foundational | 8 tasks |
| Phase 3 | US1 - Email (MVP) | 19 tasks |
| Phase 4 | US2 - WhatsApp | 12 tasks |
| Phase 5 | US3 - Web Form | 10 tasks |
| Phase 6 | US4 - Cross-Channel | 10 tasks |
| Phase 7 | US5 - Escalation | 12 tasks |
| Phase 8 | Production Deployment | 14 tasks |
| Phase 9 | Polish | 10 tasks |
| **Total** | **All Phases** | **100 tasks** |

---

## Validation

✅ All tasks follow the strict checklist format: `- [ ] T[ID] [P?] [US?] Description with file path`
✅ Each user story phase has [Story] label ([US1], [US2], etc.)
✅ Setup and Foundational phases have NO story labels
✅ All tasks include specific file paths
✅ Parallelizable tasks marked with [P]
✅ Tasks organized by user story for independent implementation
✅ Each user story is independently testable
✅ MVP scope clearly defined (Phase 1-3: Email only)
✅ Incremental delivery path documented
