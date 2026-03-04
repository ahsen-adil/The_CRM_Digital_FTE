-- Email Processing Log for Idempotency Protection
-- This table tracks processed Message-IDs to prevent duplicate ticket creation

-- Create processing log table
CREATE TABLE IF NOT EXISTS email_processing_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_id VARCHAR(500) UNIQUE NOT NULL,
    ticket_id UUID REFERENCES tickets(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    customer_email VARCHAR(255) NOT NULL,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_status VARCHAR(20) NOT NULL DEFAULT 'completed' CHECK (processing_status IN ('completed', 'failed', 'partial')),
    error_message TEXT,
    processing_time_ms INTEGER,
    sentiment_score DECIMAL(3,2),
    escalation_triggered BOOLEAN DEFAULT FALSE,
    escalation_id UUID REFERENCES escalations(id) ON DELETE SET NULL
);

-- Indexes for fast lookups
CREATE UNIQUE INDEX idx_email_log_message_id ON email_processing_log(message_id);
CREATE INDEX idx_email_log_ticket ON email_processing_log(ticket_id);
CREATE INDEX idx_email_log_customer ON email_processing_log(customer_email);
CREATE INDEX idx_email_log_processed_at ON email_processing_log(processed_at);

-- Function to check if message was already processed
CREATE OR REPLACE FUNCTION is_message_processed(p_message_id VARCHAR)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM email_processing_log
        WHERE message_id = p_message_id
          AND processing_status = 'completed'
    );
END;
$$ LANGUAGE plpgsql;

-- Function to log email processing
CREATE OR REPLACE FUNCTION log_email_processing(
    p_message_id VARCHAR,
    p_ticket_id UUID,
    p_conversation_id UUID,
    p_customer_email VARCHAR,
    p_processing_time_ms INTEGER,
    p_sentiment_score DECIMAL,
    p_escalation_triggered BOOLEAN,
    p_escalation_id UUID DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_log_id UUID;
BEGIN
    INSERT INTO email_processing_log (
        message_id, ticket_id, conversation_id, customer_email,
        processing_time_ms, sentiment_score, escalation_triggered, escalation_id
    )
    VALUES (
        p_message_id, p_ticket_id, p_conversation_id, p_customer_email,
        p_processing_time_ms, p_sentiment_score, p_escalation_triggered, p_escalation_id
    )
    RETURNING id INTO v_log_id;

    RETURN v_log_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE email_processing_log IS 'Tracks processed emails for idempotency - prevents duplicate ticket creation from same Message-ID';
COMMENT ON COLUMN email_processing_log.message_id IS 'Email Message-ID header (RFC 2822) - unique per email';
COMMENT ON COLUMN email_processing_log.processing_status IS 'completed=fully processed, failed=error occurred, partial=partially processed';
COMMENT ON COLUMN email_processing_log.processing_time_ms IS 'Total processing time in milliseconds for observability';
COMMENT ON COLUMN email_processing_log.sentiment_score IS 'Sentiment analysis score for monitoring and debugging';
COMMENT ON COLUMN email_processing_log.escalation_triggered IS 'Whether escalation was triggered for this email';
