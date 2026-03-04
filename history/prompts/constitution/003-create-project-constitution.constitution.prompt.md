---
id: 003
title: Create Project Constitution for Hackathon 5
stage: constitution
date: 2026-02-27
surface: agent
model: qwen-code
feature: none
branch: main
user: AHSEN
command: /sp.constitution
labels: ["constitution", "digital-fte", "agent-factory", "hackathon-5"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
 - .specify/memory/constitution.md
tests:
 - none
---

## Prompt

/sp.constitution

First, read the file **@The CRM Digital FTE Factory Final Hackathon 5.md** completely.

Also read the existing **QWEN.md** file and update it in memory/context.

Now, create or update the **project constitution** (foundational principles and guardrails) for the "CRM Digital FTE Factory Final Hackathon" project.

## Response snapshot

Created initial project constitution (v1.0.0) for CRM Digital FTE Factory with 7 core principles:

1. **Agent Maturity Model Compliance** - Two-stage development (Incubation → Specialization) with Qwen Coder
2. **Multi-Channel Architecture** - SMTP/IMAP, Whapi, Web Form with Kafka unified ingestion
3. **Incubation-First Development** - Discovery-driven prototyping before production code
4. **Production-Grade Tooling** - @function_tool standards with Pydantic schemas, error handling, logging
5. **Guardrails & Escalation** - NEVER/ALWAYS rules with automatic escalation triggers
6. **Performance Budgets** - Measurable targets (<3s response, >85% accuracy, <20% escalation)
7. **Database-First State Management** - PostgreSQL schema with customers, conversations, tickets, messages

Added sections for Security & Secrets Management, Development Workflow & Quality Gates, and Governance with amendment process.

## Outcome

- ✅ Impact: Constitution v1.0.0 established as foundational document for Hackathon 5 project
- 🧪 Tests: N/A (constitution creation)
- 📁 Files: .specify/memory/constitution.md created with comprehensive principles
- 🔁 Next prompts: Begin incubation phase with /sp.specify command for Customer Success FTE feature
- 🧠 Reflection: Constitution aligns with hackathon requirements and updated QWEN.md tech stack (SMTP/IMAP, Whapi, Qwen Coder)

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results: N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Create context files (company-profile.md, sample-tickets.json, escalation-rules.md, brand-voice.md) to begin incubation phase
