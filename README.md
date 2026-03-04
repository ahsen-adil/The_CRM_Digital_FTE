# Customer Success Digital FTE

**Build Your First 24/7 AI Employee: From Incubation to Production**

A multi-channel customer support AI agent that handles customer inquiries 24/7 via Email (SMTP/IMAP), WhatsApp (Whapi), and Web Form, with automatic escalation to human agents when needed.

---

## 🎯 Overview

This project implements the **Agent Maturity Model**:

- **Stage 1 - Incubation** (Hours 1-16): Prototype with Qwen Coder, MCP server, discovery
- **Stage 2 - Specialization** (Hours 16-48+): Production deployment with OpenAI Agents SDK, FastAPI, PostgreSQL, Kafka, Kubernetes

**Target**: Build a Digital FTE that operates at <$1,000/year with 24/7 availability, replacing a $75,000/year human FTE.

---

## 📋 Performance Budgets

| Metric | Target |
|--------|--------|
| Response time | <3 seconds processing, <30 seconds delivery |
| Accuracy | >85% on test set |
| Escalation rate | <20% of total tickets |
| Cross-channel ID | >95% accuracy |
| Availability | 24/7 with <1% downtime |

---

## 🏗️ Architecture

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│    Gmail     │    │   WhatsApp   │    │   Web Form   │
│   (Email)    │    │  (Messaging) │    │  (Website)   │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ SMTP/IMAP    │    │   Whapi      │    │   FastAPI    │
│   Polling    │    │   Webhook    │    │   Endpoint   │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           ▼
                 ┌─────────────────┐
                 │     Kafka       │
                 │  (Unified Ingest)│
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │  Customer Success│
                 │  FTE (Agent)     │
                 └────────┬────────┘
                          │
         ┌────────────────┼────────────────┐
         ▼                ▼                ▼
    PostgreSQL      Send Response    Escalate to Human
   (CRM/Tickets)    via Channel
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Git
- Gmail account with App Password
- Whapi.Cloud account (for WhatsApp)
- OpenAI API key

### 1. Clone and Setup

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
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
# - EMAIL_ADDRESS, EMAIL_PASSWORD (Gmail App Password)
# - WHAPI_API_KEY, WHAPI_PHONE_ID
# - OPENAI_API_KEY
# - Database and Kafka settings
```

### 3. Start Services with Docker

```bash
# Start PostgreSQL, Kafka, and Zookeeper
docker-compose up -d

# Verify services are running
docker-compose ps
```

### 4. Initialize Database

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U user -d crm_fte_db -f /docker-entrypoint-initdb.d/schema.sql
```

### 5. Run Stage 1 Incubation

```bash
# Start MCP server for prototyping
python src/agent/mcp_server.py

# Test email handler
python src/channels/email_handler.py
```

### 6. Run Stage 2 Production

```bash
# Start all services
docker-compose up -d api

# View logs
docker-compose logs -f api

# Access API documentation
open http://localhost:8000/docs
```

---

## 📁 Project Structure

```
crm_system/
├── src/                        # Stage 1: Incubation
│   ├── channels/
│   │   ├── email_handler.py    # SMTP/IMAP email integration
│   │   ├── whatsapp_handler.py # Whapi WhatsApp integration
│   │   └── web_form_handler.py # Web form API
│   ├── agent/
│   │   ├── core_agent.py       # Core agent logic
│   │   └── mcp_server.py       # MCP server with tools
│   └── web-form/               # Standalone embeddable form
│
├── production/                 # Stage 2: Specialization
│   ├── agent/
│   │   ├── customer_success_agent.py  # OpenAI SDK agent
│   │   ├── tools.py                   # @function_tool definitions
│   │   ├── prompts.py                 # System prompts
│   │   └── formatters.py              # Channel formatting
│   ├── channels/
│   │   ├── email_handler.py    # SMTP/IMAP with retry
│   │   ├── whatsapp_handler.py # Whapi webhook handlers
│   │   └── web_form_handler.py # Web form API
│   ├── workers/
│   │   ├── message_processor.py # Kafka consumer
│   │   └── metrics_collector.py # Metrics
│   ├── api/
│   │   └── main.py             # FastAPI application
│   ├── database/
│   │   ├── schema.sql          # PostgreSQL schema
│   │   ├── migrations/         # Database migrations
│   │   └── queries.py          # Database access
│   ├── tests/
│   ├── k8s/                    # Kubernetes manifests
│   ├── Dockerfile
│   └── requirements.txt
│
├── context/                    # Incubation context
│   ├── company-profile.md
│   ├── product-docs.md
│   ├── sample-tickets.json
│   ├── escalation-rules.md
│   └── brand-voice.md
│
├── tests/                      # Incubation tests
├── specs/                      # Specifications
│   └── 1-customer-success-fte/
│       ├── spec.md
│       ├── plan.md
│       ├── research.md
│       ├── data-model.md
│       ├── tasks.md
│       └── contracts/
│
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 📋 Channels

### Email (SMTP/IMAP)
- **Receiving**: IMAP polling or IDLE
- **Sending**: SMTP with STARTTLS
- **Threading**: In-Reply-To, References headers
- **Auth**: App Password (no OAuth2)

### WhatsApp (Whapi)
- **Receiving**: Webhook handlers
- **Sending**: Whapi API
- **Auth**: API key-based

### Web Form
- **Frontend**: Standalone embeddable HTML form
- **Backend**: FastAPI endpoint
- **Response**: Immediate confirmation + email

---

## 🛡️ Guardrails

**NEVER**:
- Discuss competitor products
- Promise features not in documentation
- Respond without creating a ticket
- Close tickets without sentiment check

**ALWAYS escalate when**:
- Sentiment < 0.3 (angry/frustrated)
- Pricing negotiations or refund requests
- Legal/compliance questions
- Complex issues beyond documented scope

---

## 📊 Testing

```bash
# Run incubation tests
pytest tests/ -v

# Run production tests
pytest production/tests/ -v

# End-to-end tests
pytest tests/test_email_e2e.py -v
pytest tests/test_whatsapp_e2e.py -v
pytest tests/test_webform_e2e.py -v
```

---

## 📈 Monitoring

Access metrics at: `http://localhost:8000/api/v1/metrics`

**Key Metrics**:
- Total tickets
- Open tickets
- Average response time
- AI resolution rate
- Escalation rate
- Average sentiment

---

## 📚 Documentation

- **[Specification](specs/1-customer-success-fte/spec.md)**: Feature requirements
- **[Plan](specs/1-customer-success-fte/plan.md)**: Technical architecture
- **[Research](specs/1-customer-success-fte/research.md)**: Technology decisions
- **[Data Model](specs/1-customer-success-fte/data-model.md)**: Database schema
- **[API Contracts](specs/1-customer-success-fte/contracts/)**: OpenAPI specification
- **[Quickstart](specs/1-customer-success-fte/quickstart.md)**: Detailed setup guide

---

## 🤝 Contributing

1. Create a feature branch from `1-customer-success-fte`
2. Make your changes
3. Run tests
4. Submit a pull request

---

## 📝 License

This project is part of the CRM Digital FTE Factory Final Hackathon 5.

---

## 🆘 Support

For issues with this project, please open an issue on GitHub or contact the development team.

**Built with**: Python 3.11, FastAPI, OpenAI Agents SDK, PostgreSQL, Kafka, Kubernetes
