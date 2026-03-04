# Research & Technology Decisions: Customer Success Digital FTE

**Feature**: Customer Success Digital FTE
**Branch**: `1-customer-success-fte`
**Date**: 2026-02-27
**Purpose**: Document technology decisions, rationale, and alternatives considered for all NEEDS CLARIFICATION items from Technical Context

---

## 1. SMTP/IMAP Email Integration

**Decision**: Use Python built-in `smtplib` and `imaplib` with App Password authentication for Gmail

**Rationale**:
- No OAuth2 complexity - uses simple username/password or App Password
- Built into Python standard library - no external dependencies
- Supports IMAP IDLE for real-time updates or polling for simplicity
- STARTTLS for secure transmission
- Works with Gmail, Outlook, Yahoo, and custom SMTP servers

**Alternatives Considered**:
- **Gmail API with OAuth2**: More complex setup (Google Cloud Console, credentials management), but provides better rate limits. Rejected due to complexity for hackathon timeline.
- **Third-party email services (SendGrid, Mailgun)**: Adds external dependency and cost. Rejected as overkill for single-email-address support bot.

**Implementation Notes**:
- Store credentials in `.env` file (EMAIL_ADDRESS, EMAIL_PASSWORD)
- Use App Password for Gmail (not regular password)
- Implement IMAP polling every 60 seconds or IDLE for real-time
- Use `In-Reply-To` and `References` headers for email threading

---

## 2. Whapi WhatsApp Integration

**Decision**: Use Whapi.Cloud API with webhook handlers for incoming messages

**Rationale**:
- Simpler authentication (API key-based, no OAuth2)
- Lower cost than Twilio WhatsApp API
- Supports webhook-based message reception
- Provides delivery receipts and read status
- Good documentation and Python SDK available

**Alternatives Considered**:
- **Twilio WhatsApp API**: More established, but higher cost and more complex setup. Rejected due to cost and complexity.
- **Meta WhatsApp Business API**: Direct integration with Meta, but requires business verification and has stricter approval process. Rejected for hackathon timeline.

**Implementation Notes**:
- Store API key in `.env` (WHAPI_API_KEY)
- Set up webhook endpoint in FastAPI for incoming messages
- Use Whapi SDK or direct REST API calls
- Handle message types: text, media, location, contacts

---

## 3. OpenAI Agents SDK

**Decision**: Use OpenAI Agents SDK with @function_tool decorators for production agent

**Rationale**:
- Purpose-built for AI agent workflows
- Built-in support for function calling with strict schemas
- Handles agent state management automatically
- Supports handoffs between specialized agents
- Integrates with OpenAI models natively

**Alternatives Considered**:
- **LangChain**: More flexible but adds complexity and abstraction layers. Rejected for simpler use case.
- **LlamaIndex**: Focused on RAG, not general agent workflows. Rejected as not fitting agent paradigm.
- **Custom agent framework**: Would require building state management, function calling from scratch. Rejected due to time constraints.

**Implementation Notes**:
- Define tools with `@function_tool` decorator
- Use Pydantic BaseModel for input schemas
- Implement proper error handling with fallbacks
- Add comprehensive docstrings for LLM guidance

---

## 4. PostgreSQL with pgvector

**Decision**: Use PostgreSQL 15+ with pgvector extension for semantic search

**Rationale**:
- Single database for both relational data and vector embeddings
- pgvector provides efficient vector similarity search
- No need for separate vector database (Pinecone, Weaviate)
- Supports hybrid search (keyword + vector)
- Well-documented with Python async drivers (asyncpg)

**Alternatives Considered**:
- **Separate vector database (Pinecone, Weaviate)**: Adds infrastructure complexity and cost. Rejected for unified PostgreSQL approach.
- **Elasticsearch with vector plugin**: More complex setup, overkill for simple semantic search. Rejected for pgvector simplicity.
- **SQLite with sqlite-vec**: Good for local development, but lacks production scalability. Rejected for PostgreSQL production readiness.

**Implementation Notes**:
- Install pgvector extension: `CREATE EXTENSION vector;`
- Store embeddings as `vector(1536)` for OpenAI embeddings
- Use cosine similarity: `1 - (embedding <=> query_vector)`
- Create indexes on vector columns for performance

---

## 5. Kafka Event Streaming

**Decision**: Use Kafka for unified ticket ingestion and async message processing

**Rationale**:
- Decouples channel intake from agent processing
- Provides reliable message queue with persistence
- Supports multiple consumers (agent, metrics, analytics)
- Scales horizontally with partitioning
- Industry standard for event-driven architectures

**Alternatives Considered**:
- **RabbitMQ**: Simpler but lacks Kafka's scalability and event sourcing capabilities. Rejected for less suitable event streaming model.
- **Redis Streams**: Good for simple queues, but lacks Kafka's durability and replay capabilities. Rejected for production reliability requirements.
- **AWS SQS**: Cloud-locked, adds vendor dependency. Rejected for Kubernetes-native approach.

**Implementation Notes**:
- Topics: `tickets.incoming`, `tickets.responses`, `tickets.escalations`
- Use `confluent-kafka` Python client for async consumption
- Implement consumer groups for parallel processing
- Store Kafka events for audit trail

---

## 6. FastAPI Webhooks

**Decision**: Use FastAPI for webhook handlers and web form API

**Rationale**:
- Async-first framework matches agent async requirements
- Automatic OpenAPI documentation
- Pydantic integration for request validation
- Easy webhook signature verification
- High performance (Starlette-based)

**Alternatives Considered**:
- **Flask**: Simpler but synchronous, requires Flask-RESTX for OpenAPI. Rejected for async limitations.
- **Django REST Framework**: Heavier, more complex setup. Rejected for microservice-friendly FastAPI.
- ** aiohttp**: Lower-level, requires manual routing and validation. Rejected for FastAPI's developer experience.

**Implementation Notes**:
- Use `FastAPI()` app with CORS middleware
- Define Pydantic models for request/response schemas
- Implement webhook signature verification for WhatsApp
- Use background tasks for async processing

---

## 7. Sentiment Analysis

**Decision**: Use Hugging Face transformers with pre-trained sentiment model

**Rationale**:
- High accuracy on customer support text
- Pre-trained models available (no training required)
- Supports multiple languages
- Provides confidence scores for threshold-based escalation
- Can run locally (no API dependency)

**Alternatives Considered**:
- **TextBlob**: Simpler but less accurate, especially for nuanced support queries. Rejected for lower accuracy.
- **VADER**: Good for social media, but less accurate on support tickets. Rejected for domain mismatch.
- **Cloud APIs (Google NLP, AWS Comprehend)**: Adds external dependency and cost. Rejected for local processing preference.

**Implementation Notes**:
- Model: `distilbert-base-uncased-finetuned-sst-2-english` (lightweight, accurate)
- Threshold: sentiment < 0.3 triggers escalation
- Cache results to avoid re-processing same message
- Track sentiment trend across conversation

---

## 8. Kubernetes Deployment

**Decision**: Use Kubernetes with Helm charts for production deployment

**Rationale**:
- Industry standard for container orchestration
- Supports auto-scaling based on queue depth
- Provides health checks and self-healing
- Enables rolling deployments and rollbacks
- Matches hackathon production requirements

**Alternatives Considered**:
- **Docker Compose**: Simpler but lacks orchestration and scaling. Rejected for production requirements.
- **AWS ECS**: Cloud-locked, adds vendor dependency. Rejected for Kubernetes portability.
- **Heroku/Render**: Simpler deployment but less control and higher cost at scale. Rejected for learning objectives.

**Implementation Notes**:
- Deployments: FastAPI API, Kafka consumers (workers), PostgreSQL
- Services: ClusterIP for internal, LoadBalancer/Ingress for API
- ConfigMaps for environment variables
- HorizontalPodAutoscaler based on CPU/memory or Kafka lag

---

## Summary of Technology Stack

| Component | Technology | Justification |
|-----------|-----------|---------------|
| **Language** | Python 3.11+ | Async support, rich AI/ML ecosystem |
| **Agent Framework** | OpenAI Agents SDK | Purpose-built for AI agents, function calling |
| **Email** | SMTP/IMAP (smtplib, imaplib) | Built-in, no OAuth2 complexity |
| **WhatsApp** | Whapi.Cloud | Simple API key auth, lower cost than Twilio |
| **Web Framework** | FastAPI | Async, automatic OpenAPI, Pydantic integration |
| **Database** | PostgreSQL 15+ with pgvector | Unified relational + vector storage |
| **Message Queue** | Kafka | Event streaming, decoupled processing |
| **Sentiment Analysis** | Hugging Face transformers | High accuracy, pre-trained models |
| **Deployment** | Kubernetes | Industry standard, auto-scaling, self-healing |
| **Testing** | pytest + pytest-asyncio | Async test support, fixtures |

---

## Next Steps

1. ✅ All NEEDS CLARIFICATION items resolved
2. Proceed to Phase 1: Generate data-model.md
3. Generate API contracts in contracts/ directory
4. Create quickstart.md for development setup
5. Update agent context with new technologies
