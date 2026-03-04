-- PostgreSQL Schema for Customer Success Digital FTE
-- Branch: 1-customer-success-fte
-- Date: 2026-02-27

-- Enable pgvector extension for semantic search
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Customers table
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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
    message_references JSONB,
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
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(100),
    embedding vector(1536),  -- OpenAI embedding dimension
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_knowledge_base_category ON knowledge_base(category);
CREATE INDEX idx_knowledge_base_embedding ON knowledge_base USING ivfflat (embedding vector_cosine_ops);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at on customers table
CREATE TRIGGER update_customers_updated_at
    BEFORE UPDATE ON customers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert initial ticket number counter
CREATE TABLE IF NOT EXISTS ticket_counters (
    id SERIAL PRIMARY KEY,
    year INTEGER UNIQUE NOT NULL,
    counter INTEGER DEFAULT 0
);

INSERT INTO ticket_counters (year, counter) VALUES (2026, 0)
ON CONFLICT (year) DO NOTHING;

-- Function to generate ticket number
CREATE OR REPLACE FUNCTION generate_ticket_number()
RETURNS TRIGGER AS $$
DECLARE
    year_part INTEGER;
    counter_val INTEGER;
BEGIN
    year_part := EXTRACT(YEAR FROM NEW.created_at);
    
    -- Get current counter for this year
    SELECT counter INTO counter_val
    FROM ticket_counters
    WHERE year = year_part
    FOR UPDATE;
    
    -- If no counter exists, initialize it
    IF counter_val IS NULL THEN
        counter_val := 0;
        INSERT INTO ticket_counters (year, counter) VALUES (year_part, 0);
    END IF;
    
    -- Increment counter
    counter_val := counter_val + 1;
    UPDATE ticket_counters SET counter = counter_val WHERE year = year_part;

    -- Set ticket number (use LPAD for zero-padding)
    NEW.ticket_number := 'TKT-' || year_part || '-' || LPAD(counter_val::text, 6, '0');

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-generate ticket number
CREATE TRIGGER before_insert_ticket
    BEFORE INSERT ON tickets
    FOR EACH ROW
    EXECUTE FUNCTION generate_ticket_number();
-- AI Interactions Table for Customer Success Agent
-- Tracks all AI-generated responses and their metadata

-- Create AI interactions table
CREATE TABLE IF NOT EXISTS ai_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_id UUID REFERENCES tickets(id) ON DELETE CASCADE,
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

-- Indexes for fast lookups
CREATE INDEX idx_ai_interactions_ticket ON ai_interactions(ticket_id);
CREATE INDEX idx_ai_interactions_customer ON ai_interactions(customer_email);
CREATE INDEX idx_ai_interactions_escalation ON ai_interactions(escalation_flag);
CREATE INDEX idx_ai_interactions_created ON ai_interactions(created_at);
CREATE INDEX idx_ai_interactions_category ON ai_interactions(category);

-- Function to log AI interaction
CREATE OR REPLACE FUNCTION log_ai_interaction(
    p_ticket_id UUID,
    p_customer_email VARCHAR,
    p_original_message TEXT,
    p_ai_response TEXT,
    p_sentiment_score DECIMAL,
    p_confidence_score DECIMAL,
    p_escalation_flag BOOLEAN,
    p_escalation_reason VARCHAR,
    p_category VARCHAR,
    p_priority VARCHAR,
    p_processing_time_ms INTEGER
)
RETURNS UUID AS $$
DECLARE
    v_id UUID;
BEGIN
    INSERT INTO ai_interactions (
        ticket_id, customer_email, original_message, ai_response,
        sentiment_score, confidence_score, escalation_flag, escalation_reason,
        category, priority, processing_time_ms
    )
    VALUES (
        p_ticket_id, p_customer_email, p_original_message, p_ai_response,
        p_sentiment_score, p_confidence_score, p_escalation_flag, p_escalation_reason,
        p_category, p_priority, p_processing_time_ms
    )
    RETURNING id INTO v_id;

    RETURN v_id;
END;
$$ LANGUAGE plpgsql;

-- View for AI interaction analytics
CREATE OR REPLACE VIEW ai_interaction_stats AS
SELECT
    DATE(created_at) as interaction_date,
    COUNT(*) as total_interactions,
    COUNT(CASE WHEN escalation_flag = TRUE THEN 1 END) as escalations,
    AVG(sentiment_score) as avg_sentiment,
    AVG(confidence_score) as avg_confidence,
    AVG(processing_time_ms) as avg_processing_time,
    category,
    priority
FROM ai_interactions
GROUP BY DATE(created_at), category, priority;

COMMENT ON TABLE ai_interactions IS 'Stores all AI agent interactions for auditing and analytics';
COMMENT ON COLUMN ai_interactions.ticket_id IS 'Associated ticket ID';
COMMENT ON COLUMN ai_interactions.customer_email IS 'Customer email address';
COMMENT ON COLUMN ai_interactions.original_message IS 'Original customer message';
COMMENT ON COLUMN ai_interactions.ai_response IS 'AI-generated response text';
COMMENT ON COLUMN ai_interactions.sentiment_score IS 'Detected sentiment (-1.0 to 1.0)';
COMMENT ON COLUMN ai_interactions.confidence_score IS 'AI confidence in response (0.0-1.0)';
COMMENT ON COLUMN ai_interactions.escalation_flag IS 'Whether escalation was triggered';
COMMENT ON COLUMN ai_interactions.escalation_reason IS 'Reason code for escalation';
COMMENT ON COLUMN ai_interactions.category IS 'Ticket category';
COMMENT ON COLUMN ai_interactions.priority IS 'Suggested priority';
COMMENT ON COLUMN ai_interactions.model_used IS 'AI model used for generation';
COMMENT ON COLUMN ai_interactions.tokens_used IS 'Approximate tokens consumed';
COMMENT ON COLUMN ai_interactions.processing_time_ms IS 'Processing time in milliseconds';
