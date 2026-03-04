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
