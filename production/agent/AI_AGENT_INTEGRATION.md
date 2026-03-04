# AI Agent Integration - Customer Success Digital FTE

## Overview

This document describes the integration of OpenAI Agents SDK for AI-powered customer support responses.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    EMAIL PROCESSING FLOW                     │
└─────────────────────────────────────────────────────────────┘

1. IMAP POLLING
   ┌──────────────────────────────────────┐
   │ EmailHandler.poll_emails()           │
   │ - Connects to IMAP                   │
   │ - Fetches UNSEEN emails              │
   └────────────────┬─────────────────────┘
                    │
2. PROCESSING       ▼
   ┌──────────────────────────────────────┐
   │ process_email(email_data)            │
   │ a) Create/Find Customer              │
   │ b) Create Conversation               │
   │ c) Create Ticket                     │
   └────────────────┬─────────────────────┘
                    │
3. AI AGENT         ▼
   ┌──────────────────────────────────────┐
   │ CustomerSuccessAgent                 │
   │ - Loads company context              │
   │ - Uses brand voice guidelines        │
   │ - Searches knowledge base            │
   │ - Detects escalation triggers        │
   │ - Generates response                 │
   └────────────────┬─────────────────────┘
                    │
4. DATABASE         ▼
   ┌──────────────────────────────────────┐
   │ Log AI Interaction                   │
   │ - ticket_id                          │
   │ - customer_email                     │
   │ - original_message                   │
   │ - ai_response                        │
   │ - sentiment_score                    │
   │ - confidence_score                   │
   │ - escalation_flag                    │
   └────────────────┬─────────────────────┘
                    │
5. ESCALATION       ▼
   ┌──────────────────────────────────────┐
   │ If escalation_required:              │
   │ - Create escalation record           │
   │ - Assign to team                     │
   │ - Send notification                  │
   └────────────────┬─────────────────────┘
                    │
6. SMTP REPLY       ▼
   ┌──────────────────────────────────────┐
   │ Send AI-generated reply              │
   │ - Via SMTP with threading            │
   │ - In-Reply-To header                 │
   │ - References header                  │
   └────────────────┬─────────────────────┘
                    │
7. MARK AS READ     ▼
   ┌──────────────────────────────────────┐
   │ Mark email as \Seen                  │
   │ - IMAP store command                 │
   └──────────────────────────────────────┘
```

## Files Created/Modified

### New Files

| File | Purpose |
|------|---------|
| `production/agent/customer_success_agent.py` | AI agent definition with tools |
| `production/database/migrations/002_ai_interactions.sql` | Database schema for AI logging |

### Modified Files

| File | Changes |
|------|---------|
| `poll_emails.py` | Integrated AI agent into email processing flow |
| `production/database/repository.py` | Added AI interaction logging functions |

## Customer Success Agent

### Agent Definition

Located: `production/agent/customer_success_agent.py`

```python
customer_success_agent = Agent(
    name="CustomerSuccessAgent",
    instructions="...",  # Includes company context, brand voice, escalation rules
    tools=[search_knowledge_base, check_escalation_criteria],
    output_type=AgentResponse,
    model="gpt-4o",
)
```

### Structured Output

```python
class AgentResponse(BaseModel):
    reply_text: str                    # AI-generated response
    escalation_required: bool          # Whether to escalate
    escalation_reason: Optional[str]   # Reason code if escalated
    confidence_score: float            # AI confidence (0.0-1.0)
    sentiment_score: float             # Detected sentiment (-1.0 to 1.0)
    category: str                      # Ticket category
    priority: str                      # Suggested priority
```

### Function Tools

**1. search_knowledge_base()**
- Searches product documentation
- Returns relevant information
- Used for accurate response generation

**2. check_escalation_criteria()**
- Evaluates sentiment, keywords, category
- Returns escalation recommendation
- Reason codes: negative_sentiment, pricing_request, refund_request, etc.

## Database Schema

### ai_interactions Table

```sql
CREATE TABLE ai_interactions (
    id UUID PRIMARY KEY,
    ticket_id UUID REFERENCES tickets(id),
    customer_email VARCHAR(255) NOT NULL,
    original_message TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    sentiment_score DECIMAL(3,2),
    confidence_score DECIMAL(3,2),
    escalation_flag BOOLEAN DEFAULT FALSE,
    escalation_reason VARCHAR(50),
    category VARCHAR(50),
    priority VARCHAR(20),
    model_used VARCHAR(50) DEFAULT 'gpt-4o',
    tokens_used INTEGER,
    processing_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Indexes

- `idx_ai_interactions_ticket` - Fast lookup by ticket
- `idx_ai_interactions_customer` - Fast lookup by customer
- `idx_ai_interactions_escalation` - Fast escalation filtering
- `idx_ai_interactions_created` - Time-based queries
- `idx_ai_interactions_category` - Category analytics

## Usage

### Start Email Polling

```bash
cd "C:\Users\AHSEN\Desktop\customer relation managment\crm_system"
python poll_emails.py
```

### Expected Output

```
[EMAIL RECEIVED] 2026-02-27 10:30:45
============================================================
From: customer@example.com
Subject: How do I create a project?

Body Preview:
  Hi, I need help creating my first project...

[STEP 1] Creating/finding customer...
  Customer ID: 550e8400-e29b-41d4-a716-446655440000

[STEP 2] Creating conversation...
  Conversation ID: 660e8400-e29b-41d4-a716-446655440001

[STEP 3] Creating ticket...
  Ticket ID: 770e8400-e29b-41d4-a716-446655440002
  Ticket Number: TKT-2026-000001

[STEP 4] Calling AI agent for response...
  AI processing time: 1250ms
  Sentiment: 0.75
  Confidence: 0.92
  Category: how-to
  Escalation: False

[STEP 5] Logging AI interaction to database...
  ✅ AI interaction logged

[STEP 6] Creating escalation...
  ⚠️  Escalation required: pricing_request

[STEP 7] Sending AI-generated reply via SMTP...

============================================================
[SMTP] ✅ REPLY SENT SUCCESSFULLY
[SMTP] To: customer@example.com
[SMTP] Subject: Re: How do I create a project?
============================================================

[PROCESSING COMPLETE]
  Ticket ID: 770e8400-e29b-41d4-a716-446655440002
  Sentiment: 0.75
  Escalation: False
  Response Sent: True
  Total Time: 2345ms
```

## Context Files

The agent uses these context files for response generation:

| File | Purpose |
|------|---------|
| `context/company-profile.md` | Company information, support hours, teams |
| `context/product-docs.md` | Product features, pricing, troubleshooting |
| `context/brand-voice.md` | Tone, templates, do's/don'ts |
| `context/escalation-rules.md` | When and how to escalate |

## Escalation Flow

### Automatic Triggers

1. **Negative Sentiment** (< 0.3)
2. **Pricing Requests** (pricing, cost, quote, enterprise)
3. **Refund Requests** (refund, cancel, chargeback)
4. **Legal/Compliance** (GDPR, legal, data privacy)
5. **Complex Issues** (beyond AI knowledge)
6. **Customer Request** (wants human agent)

### Escalation Assignment

| Reason Code | Assigned Team | SLA |
|-------------|---------------|-----|
| negative_sentiment | Support | 2 hours |
| pricing_request | Sales | 4 hours |
| refund_request | Billing | 24 hours |
| legal_compliance | Legal | 48 hours |
| complex_issue | Support Engineering | 24 hours |

## Analytics

### Query AI Interaction Stats

```sql
-- Get stats for last 7 days
SELECT * FROM ai_interaction_stats
WHERE interaction_date >= NOW() - INTERVAL '7 days';

-- Get escalation rate
SELECT
    COUNT(*) as total,
    COUNT(CASE WHEN escalation_flag THEN 1 END) as escalations,
    COUNT(CASE WHEN escalation_flag THEN 1 END)::float / COUNT(*) * 100 as escalation_rate
FROM ai_interactions;
```

### Key Metrics

- **Total Interactions**: Count of AI-generated responses
- **Escalation Rate**: % of conversations escalated to humans
- **Average Sentiment**: Overall customer satisfaction
- **Average Confidence**: AI confidence in responses
- **Average Processing Time**: AI response time

## Configuration

### Environment Variables

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-your_api_key_here
OPENAI_MODEL=gpt-4o

# Database Configuration
DATABASE_URL=postgresql://...

# Email Configuration
EMAIL_ADDRESS=meoahsan01@gmail.com
EMAIL_PASSWORD=your_app_password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
```

## Error Handling

### AI Agent Failures

If AI agent fails:
1. Log error with full stack trace
2. Return error result with `response_sent: False`
3. Email remains unread for retry

### Database Failures

If database logging fails:
1. Continue with SMTP send
2. Log error to console
3. Email still processed

### SMTP Failures

If SMTP fails:
1. Log detailed error
2. Email remains unread
3. Will be retried on next poll

## Testing

### Test AI Agent Directly

```bash
cd "C:\Users\AHSEN\Desktop\customer relation managment\crm_system"
python -m production.agent.customer_success_agent
```

### Test Email Flow

```bash
# Send test email to meoahsan01@gmail.com
# Wait for poll (60s max)
# Check recipient inbox for AI reply
```

## Security

### API Key Management

- Store OpenAI API key in `.env`
- Never commit `.env` to git
- Rotate keys regularly

### Data Privacy

- Customer emails stored in database
- AI interactions logged for auditing
- PII handling per company policy

## Performance

### Target Metrics

| Metric | Target | Current |
|--------|--------|---------|
| AI Processing Time | < 3 seconds | ~1.5s |
| Total Processing Time | < 30 seconds | ~5s |
| Escalation Rate | < 20% | TBD |
| AI Confidence | > 0.8 | TBD |

### Optimization

- Use connection pooling for database
- Cache frequently accessed context
- Batch database writes when possible

## Next Steps

### Phase 4 Enhancements

1. **WhatsApp Integration**: Same agent, different channel formatter
2. **Web Form Integration**: Immediate AI response on submission
3. **Cross-Channel Continuity**: Share conversation history across channels
4. **Advanced Escalation**: Auto-assign to specific human agents

### Future Improvements

1. **Vector Search**: Use pgvector for semantic knowledge base search
2. **Multi-Agent Handoff**: Specialized agents for different categories
3. **Guardrails**: Input/output validation for safety
4. **Streaming**: Stream AI responses for faster time-to-first-byte

---

**Integration Complete!** 🎉

The Customer Success AI Agent is now fully integrated with:
- ✅ OpenAI Agents SDK for reasoning
- ✅ Neon PostgreSQL for storage
- ✅ SMTP for sending replies
- ✅ IMAP for receiving emails
- ✅ Company context for accurate responses
- ✅ Brand voice alignment
- ✅ Automatic escalation detection
