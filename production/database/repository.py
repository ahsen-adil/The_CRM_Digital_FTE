"""
Database query functions for Customer Success Digital FTE.
Provides CRUD operations for all entities using asyncpg.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncpg
from production.database.queries import db_pool


# =============================================================================
# AI Interaction Queries
# =============================================================================

async def log_ai_interaction(
    ticket_id: str,
    customer_email: str,
    original_message: str,
    ai_response: str,
    sentiment_score: float,
    confidence_score: float,
    escalation_flag: bool,
    escalation_reason: Optional[str],
    category: str,
    priority: str,
    processing_time_ms: int,
    model_used: str = "gpt-4o",
    tokens_used: Optional[int] = None
) -> Dict[str, Any]:
    """
    Log an AI agent interaction.
    
    Args:
        ticket_id: Associated ticket UUID
        customer_email: Customer email address
        original_message: Original customer message
        ai_response: AI-generated response text
        sentiment_score: Detected sentiment (-1.0 to 1.0)
        confidence_score: AI confidence (0.0-1.0)
        escalation_flag: Whether escalation was triggered
        escalation_reason: Reason code for escalation
        category: Ticket category
        priority: Suggested priority
        processing_time_ms: Processing time in milliseconds
        model_used: AI model used
        tokens_used: Approximate tokens consumed
    
    Returns:
        Created AI interaction record
    """
    async with db_pool.acquire() as conn:
        interaction = await conn.fetchrow(
            """
            INSERT INTO ai_interactions (
                ticket_id, customer_email, original_message, ai_response,
                sentiment_score, confidence_score, escalation_flag, escalation_reason,
                category, priority, model_used, tokens_used, processing_time_ms
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            RETURNING *
            """,
            ticket_id, customer_email, original_message, ai_response,
            sentiment_score, confidence_score, escalation_flag, escalation_reason,
            category, priority, model_used, tokens_used, processing_time_ms
        )
        return dict(interaction) if interaction else None


async def get_ai_interactions_by_ticket(
    ticket_id: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Get AI interactions for a specific ticket."""
    async with db_pool.acquire() as conn:
        interactions = await conn.fetch(
            """
            SELECT * FROM ai_interactions
            WHERE ticket_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            ticket_id, limit
        )
        return [dict(i) for i in interactions]


async def get_ai_interaction_stats(
    days: int = 7
) -> Dict[str, Any]:
    """
    Get AI interaction statistics for the last N days.
    
    Returns:
        Dictionary with aggregated statistics
    """
    async with db_pool.acquire() as conn:
        stats = await conn.fetchrow(
            """
            SELECT
                COUNT(*) as total_interactions,
                COUNT(CASE WHEN escalation_flag = TRUE THEN 1 END) as escalations,
                AVG(sentiment_score) as avg_sentiment,
                AVG(confidence_score) as avg_confidence,
                AVG(processing_time_ms) as avg_processing_time,
                AVG(tokens_used) as avg_tokens
            FROM ai_interactions
            WHERE created_at >= NOW() - INTERVAL '1 day' * $1
            """,
            days
        )
        return dict(stats) if stats else None


# =============================================================================
# Customer Queries
# =============================================================================

async def create_customer(
    email: str,
    phone_number: Optional[str] = None,
    name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new customer or return existing one if email exists.
    
    Args:
        email: Customer email address (primary identifier)
        phone_number: WhatsApp phone number in E.164 format
        name: Customer name
    
    Returns:
        Customer record as dictionary
    """
    async with db_pool.acquire() as conn:
        # Try to find existing customer
        existing = await conn.fetchrow(
            "SELECT * FROM customers WHERE email = $1",
            email
        )
        
        if existing:
            return dict(existing)
        
        # Create new customer
        customer = await conn.fetchrow(
            """
            INSERT INTO customers (email, phone_number, name)
            VALUES ($1, $2, $3)
            RETURNING *
            """,
            email, phone_number, name
        )
        
        return dict(customer)


async def get_customer_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get customer by email address."""
    async with db_pool.acquire() as conn:
        customer = await conn.fetchrow(
            "SELECT * FROM customers WHERE email = $1",
            email
        )
        return dict(customer) if customer else None


async def get_customer_by_phone(phone_number: str) -> Optional[Dict[str, Any]]:
    """Get customer by WhatsApp phone number."""
    async with db_pool.acquire() as conn:
        customer = await conn.fetchrow(
            "SELECT * FROM customers WHERE phone_number = $1",
            phone_number
        )
        return dict(customer) if customer else None


async def update_customer_sentiment(
    customer_id: str,
    sentiment_score: float
) -> Dict[str, Any]:
    """
    Update customer's average sentiment (rolling average).
    
    Args:
        customer_id: Customer UUID
        sentiment_score: New sentiment score to incorporate
    
    Returns:
        Updated customer record
    """
    async with db_pool.acquire() as conn:
        customer = await conn.fetchrow(
            """
            UPDATE customers
            SET average_sentiment = COALESCE(
                (average_sentiment + $2) / 2,
                $2
            ),
            updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
            RETURNING *
            """,
            customer_id, sentiment_score
        )
        return dict(customer) if customer else None


# =============================================================================
# Ticket Queries
# =============================================================================

async def create_ticket(
    customer_id: str,
    channel: str,
    description: str,
    subject: Optional[str] = None,
    conversation_id: Optional[str] = None,
    priority: str = "normal",
    sentiment_score: Optional[float] = None
) -> Dict[str, Any]:
    """
    Create a new support ticket.
    Ticket number is auto-generated by database trigger.
    
    Args:
        customer_id: Customer UUID
        channel: Origin channel (email, whatsapp, web_form)
        description: Ticket description
        subject: Optional subject line
        conversation_id: Related conversation UUID
        priority: Ticket priority (low, normal, high, urgent)
        sentiment_score: Initial sentiment score
    
    Returns:
        Created ticket record with auto-generated ticket_number
    """
    async with db_pool.acquire() as conn:
        ticket = await conn.fetchrow(
            """
            INSERT INTO tickets (
                customer_id, channel, description, subject,
                conversation_id, priority, sentiment_score
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING *
            """,
            customer_id, channel, description, subject,
            conversation_id, priority, sentiment_score
        )
        return dict(ticket) if ticket else None


async def get_ticket(ticket_id: str) -> Optional[Dict[str, Any]]:
    """Get ticket by ID."""
    async with db_pool.acquire() as conn:
        ticket = await conn.fetchrow(
            "SELECT * FROM tickets WHERE id = $1",
            ticket_id
        )
        return dict(ticket) if ticket else None


async def get_ticket_by_number(ticket_number: str) -> Optional[Dict[str, Any]]:
    """Get ticket by ticket number."""
    async with db_pool.acquire() as conn:
        ticket = await conn.fetchrow(
            "SELECT * FROM tickets WHERE ticket_number = $1",
            ticket_number
        )
        return dict(ticket) if ticket else None


async def update_ticket_status(
    ticket_id: str,
    status: str,
    resolved_at: Optional[datetime] = None
) -> Dict[str, Any]:
    """Update ticket status."""
    async with db_pool.acquire() as conn:
        ticket = await conn.fetchrow(
            """
            UPDATE tickets
            SET status = $2,
                resolved_at = COALESCE($3, resolved_at),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
            RETURNING *
            """,
            ticket_id, status, resolved_at
        )
        return dict(ticket) if ticket else None


async def get_customer_tickets(customer_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Get all tickets for a customer."""
    async with db_pool.acquire() as conn:
        tickets = await conn.fetch(
            """
            SELECT * FROM tickets
            WHERE customer_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            customer_id, limit
        )
        return [dict(t) for t in tickets]


# =============================================================================
# Conversation Queries
# =============================================================================

async def create_conversation(
    customer_id: str,
    topic: Optional[str] = None,
    status: str = "open"
) -> Dict[str, Any]:
    """Create a new conversation."""
    async with db_pool.acquire() as conn:
        conversation = await conn.fetchrow(
            """
            INSERT INTO conversations (customer_id, topic, status)
            VALUES ($1, $2, $3)
            RETURNING *
            """,
            customer_id, topic, status
        )
        return dict(conversation) if conversation else None


async def get_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
    """Get conversation by ID."""
    async with db_pool.acquire() as conn:
        conversation = await conn.fetchrow(
            "SELECT * FROM conversations WHERE id = $1",
            conversation_id
        )
        return dict(conversation) if conversation else None


async def get_active_conversation(customer_id: str) -> Optional[Dict[str, Any]]:
    """Get active (open/pending) conversation for a customer."""
    async with db_pool.acquire() as conn:
        conversation = await conn.fetchrow(
            """
            SELECT * FROM conversations
            WHERE customer_id = $1
              AND status IN ('open', 'pending')
            ORDER BY last_activity_at DESC
            LIMIT 1
            """,
            customer_id
        )
        return dict(conversation) if conversation else None


async def update_conversation_status(
    conversation_id: str,
    status: str,
    resolution_status: Optional[str] = None
) -> Dict[str, Any]:
    """Update conversation status."""
    async with db_pool.acquire() as conn:
        conversation = await conn.fetchrow(
            """
            UPDATE conversations
            SET status = $2,
                resolution_status = COALESCE($3, resolution_status),
                last_activity_at = CURRENT_TIMESTAMP
            WHERE id = $1
            RETURNING *
            """,
            conversation_id, status, resolution_status
        )
        return dict(conversation) if conversation else None


async def add_channel_to_conversation(
    conversation_id: str,
    channel: str
) -> Dict[str, Any]:
    """Add channel to conversation's channel_history."""
    async with db_pool.acquire() as conn:
        conversation = await conn.fetchrow(
            """
            UPDATE conversations
            SET channel_history = channel_history || $2::jsonb,
                last_activity_at = CURRENT_TIMESTAMP
            WHERE id = $1
            RETURNING *
            """,
            conversation_id, f'["{channel}"]'
        )
        return dict(conversation) if conversation else None


# =============================================================================
# Message Queries
# =============================================================================

async def create_message(
    message_id: str,
    conversation_id: str,
    channel: str,
    direction: str,
    content: str,
    ticket_id: Optional[str] = None,
    content_html: Optional[str] = None,
    sentiment_score: Optional[float] = None,
    sentiment_confidence: Optional[float] = None,
    in_reply_to: Optional[str] = None,
    references: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a new message.
    
    Args:
        message_id: Unique message ID from channel (Email Message-ID, WhatsApp ID)
        conversation_id: Parent conversation UUID
        channel: Message channel (email, whatsapp, web_form)
        direction: Message direction (inbound, outbound)
        content: Message content (plain text)
        ticket_id: Related ticket UUID
        content_html: HTML version of content
        sentiment_score: Message sentiment (-1.0 to 1.0)
        sentiment_confidence: Confidence in sentiment (0.0 to 1.0)
        in_reply_to: Message ID this is replying to
        references: Array of message IDs in thread
        metadata: Channel-specific metadata
    
    Returns:
        Created message record
    """
    async with db_pool.acquire() as conn:
        message = await conn.fetchrow(
            """
            INSERT INTO messages (
                message_id, conversation_id, channel, direction,
                content, ticket_id, content_html, sentiment_score,
                sentiment_confidence, in_reply_to, references, metadata
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING *
            """,
            message_id, conversation_id, channel, direction,
            content, ticket_id, content_html, sentiment_score,
            sentiment_confidence, in_reply_to,
            references, metadata
        )
        return dict(message) if message else None


async def get_message(message_id: str) -> Optional[Dict[str, Any]]:
    """Get message by ID."""
    async with db_pool.acquire() as conn:
        message = await conn.fetchrow(
            "SELECT * FROM messages WHERE message_id = $1",
            message_id
        )
        return dict(message) if message else None


async def get_conversation_messages(
    conversation_id: str,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Get all messages in a conversation."""
    async with db_pool.acquire() as conn:
        messages = await conn.fetch(
            """
            SELECT * FROM messages
            WHERE conversation_id = $1
            ORDER BY sent_at ASC
            LIMIT $2
            """,
            conversation_id, limit
        )
        return [dict(m) for m in messages]


# =============================================================================
# Knowledge Base Queries
# =============================================================================

async def search_knowledge_base(
    query: str,
    category: Optional[str] = None,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Search knowledge base using semantic search with pgvector.
    
    Args:
        query: Search query text
        category: Optional category filter
        limit: Maximum results to return
    
    Returns:
        List of relevant knowledge base articles with similarity scores
    """
    async with db_pool.acquire() as conn:
        # For now, use text search (vector search requires embedding generation)
        # This will be enhanced with pgvector in production
        if category:
            results = await conn.fetch(
                """
                SELECT id, title, content, category,
                       ts_rank(to_tsvector('english', content), plainto_tsquery('english', $1)) as relevance
                FROM knowledge_base
                WHERE category = $2
                  AND to_tsvector('english', content) @@ plainto_tsquery('english', $1)
                ORDER BY relevance DESC
                LIMIT $3
                """,
                query, category, limit
            )
        else:
            results = await conn.fetch(
                """
                SELECT id, title, content, category,
                       ts_rank(to_tsvector('english', content), plainto_tsquery('english', $1)) as relevance
                FROM knowledge_base
                WHERE to_tsvector('english', content) @@ plainto_tsquery('english', $1)
                ORDER BY relevance DESC
                LIMIT $2
                """,
                query, limit
            )
        
        return [dict(r) for r in results]


async def add_knowledge_base_article(
    title: str,
    content: str,
    category: Optional[str] = None,
    embedding: Optional[List[float]] = None
) -> Dict[str, Any]:
    """Add article to knowledge base."""
    async with db_pool.acquire() as conn:
        if embedding:
            article = await conn.fetchrow(
                """
                INSERT INTO knowledge_base (title, content, category, embedding)
                VALUES ($1, $2, $3, $4)
                RETURNING *
                """,
                title, content, category, embedding
            )
        else:
            article = await conn.fetchrow(
                """
                INSERT INTO knowledge_base (title, content, category)
                VALUES ($1, $2, $3)
                RETURNING *
                """,
                title, content, category
            )
        return dict(article) if article else None


# =============================================================================
# Utility Queries
# =============================================================================

async def get_customer_history(customer_id: str) -> Dict[str, Any]:
    """
    Get complete customer history including conversations, tickets, and messages.
    
    Args:
        customer_id: Customer UUID
    
    Returns:
        Dictionary with customer, conversations, tickets, and metrics
    """
    customer = await get_customer_by_email("")  # Will be replaced by customer_id lookup
    
    async with db_pool.acquire() as conn:
        # Get customer by ID
        customer = await conn.fetchrow(
            "SELECT * FROM customers WHERE id = $1",
            customer_id
        )
        
        if not customer:
            return None
        
        # Get conversations
        conversations = await conn.fetch(
            "SELECT * FROM conversations WHERE customer_id = $1 ORDER BY opened_at DESC",
            customer_id
        )
        
        # Get tickets
        tickets = await conn.fetch(
            "SELECT * FROM tickets WHERE customer_id = $1 ORDER BY created_at DESC LIMIT 20",
            customer_id
        )
        
        return {
            "customer": dict(customer),
            "conversations": [dict(c) for c in conversations],
            "tickets": [dict(t) for t in tickets],
            "total_tickets": len(tickets),
            "average_sentiment": customer["average_sentiment"]
        }
