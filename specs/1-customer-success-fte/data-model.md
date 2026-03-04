# Data Model: Customer Success Digital FTE

**Feature**: Customer Success Digital FTE
**Branch**: `1-customer-success-fte`
**Date**: 2026-02-27
**Purpose**: Define database schema, entities, relationships, and validation rules

---

## Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│  Customer   │───────│ Conversation│───────│   Ticket    │
└─────────────┘  1:N  └─────────────┘  1:N  └─────────────┘
      │                                       │
      │ 1:N                                   │ 1:N
      │                                       │
      ▼                                       ▼
┌─────────────┐                       ┌─────────────┐
│   Message   │                       │ Escalation  │
└─────────────┘                       └─────────────┘
```

---

## Entity Definitions

### Customer

Represents a unique customer identified by email address across all communication channels.

**Fields**:
- `id` (UUID, primary key): Unique customer identifier
- `email` (VARCHAR(255), unique, not null): Primary identifier, used for cross-channel matching
- `phone_number` (VARCHAR(20), nullable): WhatsApp phone number (+1234567890 format)
- `name` (VARCHAR(255), nullable): Customer name extracted from messages
- `total_tickets` (INTEGER, default 0): Count of tickets created
- `average_sentiment` (DECIMAL(3,2), nullable): Rolling average sentiment score (-1.0 to 1.0)
- `preferred_channel` (VARCHAR(20), default 'email'): Most frequently used channel
- `created_at` (TIMESTAMP, default now()): Customer profile creation timestamp
- `updated_at` (TIMESTAMP, default now()): Last profile update timestamp

**Validation Rules**:
- Email MUST match RFC 5322 email format
- Phone number MUST be in E.164 format (+[country code][number]) if provided
- Average sentiment MUST be between -1.0 and 1.0
- Total tickets MUST be non-negative

**Indexes**:
- UNIQUE INDEX on `email`
- INDEX on `phone_number`
- INDEX on `created_at`

---

### Conversation

Represents a thread of related messages across channels, maintaining conversation continuity.

**Fields**:
- `id` (UUID, primary key): Unique conversation identifier
- `customer_id` (UUID, foreign key → Customer.id, not null): Customer who owns this conversation
- `topic` (VARCHAR(500), nullable): Auto-generated topic summary
- `status` (VARCHAR(20), not null): Current status (open, pending, resolved, escalated, closed)
- `channel_history` (JSONB, default []): Array of channels used in conversation
- `resolution_status` (VARCHAR(20), default 'unresolved'): unresolved, resolved, escalated
- `sentiment_trend` (JSONB, nullable): Array of sentiment scores over time
- `opened_at` (TIMESTAMP, default now()): Conversation start timestamp
- `resolved_at` (TIMESTAMP, nullable): When conversation was resolved
- `last_activity_at` (TIMESTAMP, default now()): Last message or update timestamp

**Validation Rules**:
- Status MUST be one of: open, pending, resolved, escalated, closed
- Resolution status MUST be one of: unresolved, resolved, escalated
- Channel history MUST contain at least one channel
- Sentiment trend values MUST be between -1.0 and 1.0
- Resolved_at MUST be NULL if status is not 'resolved' or 'closed'

**Relationships**:
- Belongs to one Customer
- Has many Messages
- Has one Ticket (optional, created when escalation needed)

**Indexes**:
- INDEX on `customer_id`
- INDEX on `status`
- INDEX on `last_activity_at`
- INDEX on `resolution_status`

---

### Ticket

Represents a support inquiry with tracking across its lifecycle.

**Fields**:
- `id` (UUID, primary key): Unique ticket identifier
- `ticket_number` (VARCHAR(20), unique, not null): Human-readable ticket ID (e.g., TKT-2026-000123)
- `customer_id` (UUID, foreign key → Customer.id, not null): Customer who created ticket
- `conversation_id` (UUID, foreign key → Conversation.id, nullable): Related conversation if exists
- `channel` (VARCHAR(20), not null): Origin channel (email, whatsapp, web_form)
- `subject` (VARCHAR(500), nullable): Ticket subject/summary
- `description` (TEXT, not null): Initial customer message or issue description
- `priority` (VARCHAR(20), default 'normal'): low, normal, high, urgent
- `status` (VARCHAR(20), not null): open, in_progress, pending_customer, escalated, resolved, closed
- `sentiment_score` (DECIMAL(3,2), nullable): Initial message sentiment (-1.0 to 1.0)
- `assigned_to` (VARCHAR(255), nullable): Human agent email if assigned
- `escalation_reason` (VARCHAR(500), nullable): Why ticket was escalated
- `created_at` (TIMESTAMP, default now()): Ticket creation timestamp
- `first_response_at` (TIMESTAMP, nullable): When first response was sent
- `resolved_at` (TIMESTAMP, nullable): When ticket was resolved
- `closed_at` (TIMESTAMP, nullable): When ticket was closed

**Validation Rules**:
- Channel MUST be one of: email, whatsapp, web_form
- Priority MUST be one of: low, normal, high, urgent
- Status MUST be one of: open, in_progress, pending_customer, escalated, resolved, closed
- Sentiment score MUST be between -1.0 and 1.0 if provided
- Ticket number MUST be unique and follow format TKT-YYYY-NNNNNN
- First response at MUST be after created_at
- Resolved at MUST be after first response at if both exist

**Relationships**:
- Belongs to one Customer
- Optionally belongs to one Conversation
- Has zero or one Escalation

**Indexes**:
- UNIQUE INDEX on `ticket_number`
- INDEX on `customer_id`
- INDEX on `conversation_id`
- INDEX on `channel`
- INDEX on `status`
- INDEX on `priority`
- INDEX on `created_at`

---

### Message

Represents a single customer or agent message within a conversation.

**Fields**:
- `id` (UUID, primary key): Unique message identifier
- `message_id` (VARCHAR(500), unique, not null): Original message ID from channel (Email Message-ID, WhatsApp message ID)
- `conversation_id` (UUID, foreign key → Conversation.id, not null): Parent conversation
- `ticket_id` (UUID, foreign key → Ticket.id, nullable): Related ticket if exists
- `channel` (VARCHAR(20), not null): Message channel (email, whatsapp, web_form)
- `direction` (VARCHAR(10), not null): inbound (customer→system) or outbound (system→customer)
- `content` (TEXT, not null): Message content (plain text)
- `content_html` (TEXT, nullable): HTML version for email messages
- `sentiment_score` (DECIMAL(3,2), nullable): Message sentiment (-1.0 to 1.0)
- `sentiment_confidence` (DECIMAL(3,2), nullable): Confidence in sentiment score (0.0 to 1.0)
- `topics` (JSONB, nullable): Auto-detected topics/tags
- `metadata` (JSONB, nullable): Channel-specific metadata (headers, attachments info)
- `in_reply_to` (VARCHAR(500), nullable): Message ID this is replying to (for threading)
- `references` (JSONB, nullable): Array of message IDs in thread (for email)
- `sent_at` (TIMESTAMP, default now()): When message was sent/received
- `delivered_at` (TIMESTAMP, nullable): When message was delivered (for outbound)
- `read_at` (TIMESTAMP, nullable): When message was read by recipient

**Validation Rules**:
- Channel MUST be one of: email, whatsapp, web_form
- Direction MUST be one of: inbound, outbound
- Sentiment score MUST be between -1.0 and 1.0 if provided
- Sentiment confidence MUST be between 0.0 and 1.0 if provided
- Content MUST NOT be empty
- Message ID MUST be unique across all messages

**Relationships**:
- Belongs to one Conversation
- Optionally belongs to one Ticket

**Indexes**:
- UNIQUE INDEX on `message_id`
- INDEX on `conversation_id`
- INDEX on `ticket_id`
- INDEX on `channel`
- INDEX on `direction`
- INDEX on `sent_at`

---

### Escalation

Represents a handoff from AI agent to human agent.

**Fields**:
- `id` (UUID, primary key): Unique escalation identifier
- `escalation_number` (VARCHAR(20), unique, not null): Human-readable escalation ID (e.g., ESC-2026-00001)
- `ticket_id` (UUID, foreign key → Ticket.id, not null): Ticket being escalated
- `reason_code` (VARCHAR(50), not null): Reason for escalation (negative_sentiment, pricing_request, refund_request, legal_compliance, complex_issue, knowledge_gap, customer_request)
- `reason_details` (TEXT, nullable): Detailed explanation of why escalation needed
- `assigned_team` (VARCHAR(100), nullable): Team to handle escalation (sales, billing, support, legal)
- `assigned_to` (VARCHAR(255), nullable): Specific human agent email if assigned
- `priority` (VARCHAR(20), default 'normal'): low, normal, high, urgent
- `status` (VARCHAR(20), not null): pending, assigned, in_progress, resolved, closed
- `conversation_context` (JSONB, nullable): Snapshot of conversation at escalation time
- `sentiment_trend` (JSONB, nullable): Sentiment scores leading to escalation
- `attempted_resolutions` (JSONB, nullable): What the AI tried before escalating
- `created_at` (TIMESTAMP, default now()): Escalation creation timestamp
- `assigned_at` (TIMESTAMP, nullable): When human agent was assigned
- `resolved_at` (TIMESTAMP, nullable): When escalation was resolved

**Validation Rules**:
- Reason code MUST be one of: negative_sentiment, pricing_request, refund_request, legal_compliance, complex_issue, knowledge_gap, customer_request
- Priority MUST be one of: low, normal, high, urgent
- Status MUST be one of: pending, assigned, in_progress, resolved, closed
- Assigned team MUST be one of: sales, billing, support, legal, general (if provided)

**Relationships**:
- Belongs to one Ticket

**Indexes**:
- UNIQUE INDEX on `escalation_number`
- INDEX on `ticket_id`
- INDEX on `reason_code`
- INDEX on `assigned_team`
- INDEX on `status`
- INDEX on `created_at`

---

## Database Schema (PostgreSQL)

```sql
-- Enable pgvector extension for semantic search
CREATE EXTENSION IF NOT EXISTS vector;

-- Customers table
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    phone_number VARCHAR(20),
    name VARCHAR(255),
    total_tickets INTEGER DEFAULT 0,
    average_sentiment DECIMAL(3,2),
    preferred_channel VARCHAR(20) DEFAULT 'email',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_phone ON customers(phone_number);
CREATE INDEX idx_customers_created ON customers(created_at);

-- Conversations table
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    topic VARCHAR(500),
    status VARCHAR(20) NOT NULL CHECK (status IN ('open', 'pending', 'resolved', 'escalated', 'closed')),
    channel_history JSONB DEFAULT '[]',
    resolution_status VARCHAR(20) DEFAULT 'unresolved' CHECK (resolution_status IN ('unresolved', 'resolved', 'escalated')),
    sentiment_trend JSONB,
    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_conversations_customer ON conversations(customer_id);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_activity ON conversations(last_activity_at);
CREATE INDEX idx_conversations_resolution ON conversations(resolution_status);

-- Tickets table
CREATE TABLE tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_number VARCHAR(20) UNIQUE NOT NULL,
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('email', 'whatsapp', 'web_form')),
    subject VARCHAR(500),
    description TEXT NOT NULL,
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    status VARCHAR(20) NOT NULL CHECK (status IN ('open', 'in_progress', 'pending_customer', 'escalated', 'resolved', 'closed')),
    sentiment_score DECIMAL(3,2),
    assigned_to VARCHAR(255),
    escalation_reason VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    first_response_at TIMESTAMP,
    resolved_at TIMESTAMP,
    closed_at TIMESTAMP
);

CREATE UNIQUE INDEX idx_tickets_number ON tickets(ticket_number);
CREATE INDEX idx_tickets_customer ON tickets(customer_id);
CREATE INDEX idx_tickets_conversation ON tickets(conversation_id);
CREATE INDEX idx_tickets_channel ON tickets(channel);
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_priority ON tickets(priority);
CREATE INDEX idx_tickets_created ON tickets(created_at);

-- Messages table
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id VARCHAR(500) UNIQUE NOT NULL,
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    ticket_id UUID REFERENCES tickets(id) ON DELETE SET NULL,
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('email', 'whatsapp', 'web_form')),
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('inbound', 'outbound')),
    content TEXT NOT NULL,
    content_html TEXT,
    sentiment_score DECIMAL(3,2),
    sentiment_confidence DECIMAL(3,2),
    topics JSONB,
    metadata JSONB,
    in_reply_to VARCHAR(500),
    references JSONB,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivered_at TIMESTAMP,
    read_at TIMESTAMP
);

CREATE UNIQUE INDEX idx_messages_id ON messages(message_id);
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_ticket ON messages(ticket_id);
CREATE INDEX idx_messages_channel ON messages(channel);
CREATE INDEX idx_messages_direction ON messages(direction);
CREATE INDEX idx_messages_sent ON messages(sent_at);

-- Escalations table
CREATE TABLE escalations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    escalation_number VARCHAR(20) UNIQUE NOT NULL,
    ticket_id UUID NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    reason_code VARCHAR(50) NOT NULL CHECK (reason_code IN ('negative_sentiment', 'pricing_request', 'refund_request', 'legal_compliance', 'complex_issue', 'knowledge_gap', 'customer_request')),
    reason_details TEXT,
    assigned_team VARCHAR(100),
    assigned_to VARCHAR(255),
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'assigned', 'in_progress', 'resolved', 'closed')),
    conversation_context JSONB,
    sentiment_trend JSONB,
    attempted_resolutions JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_at TIMESTAMP,
    resolved_at TIMESTAMP
);

CREATE UNIQUE INDEX idx_escalations_number ON escalations(escalation_number);
CREATE INDEX idx_escalations_ticket ON escalations(ticket_id);
CREATE INDEX idx_escalations_reason ON escalations(reason_code);
CREATE INDEX idx_escalations_team ON escalations(assigned_team);
CREATE INDEX idx_escalations_status ON escalations(status);
CREATE INDEX idx_escalations_created ON escalations(created_at);

-- Knowledge base table (for semantic search)
CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(100),
    embedding vector(1536),  -- OpenAI embedding dimension
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_knowledge_base_category ON knowledge_base(category);
CREATE INDEX idx_knowledge_base_embedding ON knowledge_base USING ivfflat (embedding vector_cosine_ops);
```

---

## State Transitions

### Ticket Status Flow

```
open → in_progress → pending_customer → resolved → closed
                      ↓                      ↓
                  escalated ←────────────────┘
```

### Conversation Status Flow

```
open → pending → resolved → closed
         ↓
     escalated → resolved → closed
```

### Escalation Status Flow

```
pending → assigned → in_progress → resolved → closed
```

---

## Validation Rules Summary

| Entity | Field | Validation |
|--------|-------|------------|
| Customer | email | RFC 5322 format, unique |
| Customer | phone_number | E.164 format (+1234567890) |
| Customer | average_sentiment | Range: -1.0 to 1.0 |
| Ticket | channel | Enum: email, whatsapp, web_form |
| Ticket | priority | Enum: low, normal, high, urgent |
| Ticket | status | Enum: open, in_progress, pending_customer, escalated, resolved, closed |
| Message | sentiment_score | Range: -1.0 to 1.0 |
| Message | sentiment_confidence | Range: 0.0 to 1.0 |
| Escalation | reason_code | Enum: negative_sentiment, pricing_request, refund_request, legal_compliance, complex_issue, knowledge_gap, customer_request |

---

## Next Steps

1. ✅ Data model complete with all entities from spec
2. Generate API contracts in `contracts/` directory
3. Create database migrations for schema deployment
4. Implement repository layer with asyncpg
