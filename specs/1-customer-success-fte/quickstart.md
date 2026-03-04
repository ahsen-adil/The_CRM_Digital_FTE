# Quickstart Guide: Customer Success Digital FTE

**Feature**: Customer Success Digital FTE
**Branch**: `1-customer-success-fte`
**Purpose**: Get started with local development and testing

---

## Prerequisites

- Python 3.11 or higher
- PostgreSQL 15+ with pgvector extension
- Docker and Docker Compose (for local Kafka)
- Git
- Whapi.Cloud account (for WhatsApp integration)
- Gmail account with App Password enabled (for email integration)

---

## 1. Clone and Setup

```bash
# Navigate to project root
cd crm_system

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r production/requirements.txt
```

---

## 2. Environment Configuration

Create a `.env` file in the project root:

```env
# Email Configuration (SMTP/IMAP)
EMAIL_ADDRESS=yourname@gmail.com
EMAIL_PASSWORD=your_app_password  # Gmail App Password, not regular password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
IMAP_HOST=imap.gmail.com
IMAP_PORT=993

# WhatsApp Configuration (Whapi)
WHAPI_API_KEY=your_whapi_api_key
WHAPI_PHONE_ID=your_whatsapp_phone_id

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/crm_fte_db
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=crm_fte_db

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_INCOMING=tickets.incoming
KAFKA_TOPIC_RESPONSES=tickets.responses

# OpenAI Configuration
OPENAI_API_KEY=sk-your_openai_api_key

# Application Configuration
ENVIRONMENT=development
LOG_LEVEL=DEBUG
POLL_INTERVAL=60  # Email polling interval in seconds
```

**Security Note**: Never commit `.env` to git. It's already in `.gitignore`.

---

## 3. Database Setup

### Option A: Using Docker Compose (Recommended)

```bash
# Start PostgreSQL with pgvector
docker-compose up -d postgres

# Wait for database to be ready
sleep 10

# Run migrations
python production/database/migrations/001_initial_schema.py
```

### Option B: Manual PostgreSQL Setup

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE crm_fte_db;

# Connect to database
\c crm_fte_db;

# Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

# Run schema
\i production/database/schema.sql

# Exit
\q
```

---

## 4. Kafka Setup (Local Development)

```bash
# Start Kafka using Docker Compose
docker-compose up -d kafka zookeeper

# Verify Kafka is running
docker-compose ps

# Create topics (if not auto-created)
docker-compose exec kafka kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic tickets.incoming \
  --partitions 3 \
  --replication-factor 1

docker-compose exec kafka kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic tickets.responses \
  --partitions 3 \
  --replication-factor 1
```

---

## 5. Context Files Setup (Incubation Phase)

Create the `context/` directory with required files:

```bash
mkdir context
```

### context/company-profile.md

```markdown
# Company Profile

**Company Name**: TechSaaS Inc.
**Product**: CloudManage - Project Management SaaS
**Target Market**: Small to medium businesses (10-500 employees)
**Support Hours**: 24/7 (automated), Human agents 9am-6pm EST

**Brand Voice**:
- Friendly and approachable
- Professional but not stiff
- Empathetic to customer frustrations
- Solution-oriented
```

### context/product-docs.md

```markdown
# Product Documentation

## CloudManage Features

### 1. Project Management
- Create and manage projects
- Assign tasks to team members
- Track progress with Kanban boards
- Gantt charts for timeline visualization

### 2. Team Collaboration
- Real-time chat within tasks
- File sharing and attachments
- @mentions for notifications
- Activity feed

### 3. Time Tracking
- Start/stop timer on tasks
- Manual time entry
- Timesheet reports
- Billable hours tracking

### 4. Reporting
- Project status reports
- Team workload reports
- Time tracking reports
- Custom report builder

## Pricing Plans

### Starter ($29/month)
- Up to 5 users
- 10 projects
- 1GB storage
- Email support

### Pro ($79/month)
- Up to 20 users
- Unlimited projects
- 10GB storage
- Priority support
- Time tracking
- Gantt charts

### Enterprise (Custom pricing)
- Unlimited users
- Unlimited everything
- Dedicated support
- Custom integrations
- SSO/SAML
```

### context/sample-tickets.json

```json
{
  "tickets": [
    {
      "id": 1,
      "channel": "email",
      "subject": "How do I create a new project?",
      "body": "Hi, I just signed up and I'm not sure how to create my first project. Can you help?",
      "expected_category": "how_to",
      "expected_escalate": false
    },
    {
      "id": 2,
      "channel": "whatsapp",
      "body": "My team can't see the files I uploaded. Bug?",
      "expected_category": "bug_report",
      "expected_escalate": false
    },
    {
      "id": 3,
      "channel": "email",
      "subject": "Refund request",
      "body": "I'm not satisfied with the product. I want a refund.",
      "expected_category": "refund",
      "expected_escalate": true
    },
    {
      "id": 4,
      "channel": "web_form",
      "subject": "Pricing for 100 users",
      "body": "We're interested in your product for our company of 100 employees. What would be the cost?",
      "expected_category": "pricing",
      "expected_escalate": true
    },
    {
      "id": 5,
      "channel": "email",
      "subject": "This is ridiculous!!!",
      "body": "I've been waiting for 3 days and still no response! This is the worst support I've ever experienced!",
      "expected_category": "complaint",
      "expected_sentiment": -0.8,
      "expected_escalate": true
    }
  ]
}
```

### context/escalation-rules.md

```markdown
# Escalation Rules

## Automatic Escalation Triggers

### 1. Negative Sentiment
- Sentiment score < 0.3
- Keywords: "angry", "frustrated", "disappointed", "ridiculous", "worst"
- Multiple exclamation marks or ALL CAPS

### 2. Pricing Requests
- Any mention of "pricing", "cost", "quote", "enterprise"
- Questions about discounts or negotiations
- Bulk licensing inquiries

### 3. Refund Requests
- Any mention of "refund", "cancel", "chargeback"
- Dissatisfaction with product
- Billing disputes

### 4. Legal/Compliance
- GDPR requests
- Data privacy concerns
- Terms of service questions
- Legal threats

### 5. Complex Technical Issues
- Bug reports that require engineering
- Integration requests
- Feature requests not in documentation

## Escalation Assignment

| Reason Code | Assigned Team | SLA |
|-------------|---------------|-----|
| negative_sentiment | Support | 2 hours |
| pricing_request | Sales | 4 hours |
| refund_request | Billing | 24 hours |
| legal_compliance | Legal | 48 hours |
| complex_issue | Support Engineering | 24 hours |
```

### context/brand-voice.md

```markdown
# Brand Voice Guidelines

## Tone

**Primary**: Friendly, Helpful, Professional

**Do**:
- Use contractions (we're, you'll, let's)
- Start with warm greetings
- Acknowledge customer feelings
- Provide clear next steps
- End with offer for further help

**Don't**:
- Use overly formal language
- Sound robotic or scripted
- Make promises we can't keep
- Discuss competitors
- Use technical jargon without explanation

## Response Templates

### Email (Formal, Detailed)

```
Hi [Name],

Thank you for reaching out to CloudManage support!

[Detailed answer with 2-3 paragraphs, examples, screenshots if needed]

If you have any other questions, feel free to ask!

Best regards,
CloudManage Support Team
```

### WhatsApp (Conversational, Concise)

```
Hi [Name]! 👋 

[Quick answer in 1-2 sentences]

Need help with anything else?
```

### Web Form (Semi-formal)

```
Hi [Name],

Thanks for contacting us!

[Clear answer with actionable steps]

Best,
CloudManage Team
```
```

---

## 6. Run Incubation Phase (Stage 1)

```bash
# Start the incubation prototype
python src/agent/mcp_server.py

# In another terminal, test email handler
python src/channels/email_handler.py

# Test WhatsApp webhook (use ngrok for local testing)
ngrok http 8000
```

---

## 7. Run Production (Stage 2)

```bash
# Start all services with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f agent
docker-compose logs -f worker
docker-compose logs -f api

# Run tests
pytest production/tests/ -v

# Check metrics
curl http://localhost:8000/api/v1/metrics
```

---

## 8. Testing

### Run Unit Tests

```bash
pytest production/tests/test_agent.py -v
pytest production/tests/test_channels.py -v
pytest production/tests/test_e2e.py -v
```

### Test Email Integration

```bash
# Send test email
python tests/manual/test_email.py
```

### Test WhatsApp Webhook

```bash
# Use ngrok to expose local webhook
ngrok http 8000

# Configure Whapi webhook to point to ngrok URL
# Send test message from WhatsApp
```

---

## Common Issues

### Database Connection Error

```
Error: could not connect to server
```

**Solution**: Ensure PostgreSQL is running:
```bash
docker-compose ps  # Check if postgres container is up
# OR
pg_isready -h localhost -p 5432
```

### Kafka Connection Error

```
KafkaConnectionError: Unable to connect to broker
```

**Solution**: Restart Kafka:
```bash
docker-compose restart kafka
```

### Email Authentication Error

```
smtplib.SMTPAuthenticationError: (535, b'5.7.8 Username and Password not accepted')
```

**Solution**: 
1. Enable 2FA on Gmail account
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use App Password in `.env`, not regular password

### Whapi API Error

```
WhapiError: Invalid API key
```

**Solution**: 
1. Verify API key in Whapi.Cloud dashboard
2. Ensure API key has correct permissions
3. Check Whapi.Cloud service status

---

## Next Steps

1. ✅ Complete local setup
2. Run incubation phase exercises (see Hackathon 5 document)
3. Document discoveries in `specs/discovery-log.md`
4. Build MCP server with 5+ tools
5. Define agent skills manifest
6. Transition to production (Stage 2)

---

## Resources

- [Hackathon 5 Document](../../The%20CRM%20Digital%20FTE%20Factory%20Final%20Hackathon%205.md)
- [Constitution](../../.specify/memory/constitution.md)
- [OpenAI Agents SDK Docs](https://openai.github.io/openai-agents-python/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Whapi.Cloud Docs](https://docs.whapi.cloud/)
- [PostgreSQL pgvector](https://github.com/pgvector/pgvector)
