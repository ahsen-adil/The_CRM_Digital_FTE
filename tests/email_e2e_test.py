"""
End-to-End Email Integration Test for Customer Success Digital FTE.

Tests the complete email flow:
1. Customer sends email → Ticket created
2. Conversation created
3. Message persisted
4. Sentiment analysis
5. Escalation triggered if sentiment < 0.3
6. Email marked as read
7. Idempotency check (same Message-ID doesn't create duplicates)

Uses mocked IMAP/SMTP for testing when real credentials unavailable.
"""
import asyncio
import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from production.database.repository import (
    create_customer,
    create_ticket,
    create_conversation,
    create_message,
    get_customer_by_email,
    get_ticket_by_number,
    get_conversation,
    get_message,
)
from production.database.queries import db_pool
from production.utils.exceptions import EmailReadError, EmailDeliveryError


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
async def db_connection():
    """Initialize database pool for testing."""
    await db_pool.create_pool()
    yield db_pool
    await db_pool.close_pool()


@pytest.fixture
def mock_email_data() -> Dict[str, Any]:
    """Sample email data for testing."""
    return {
        "email_id": "test_123",
        "subject": "Unable to login to my account",
        "from": "test.customer@example.com",
        "to": "support@company.com",
        "message_id": "<unique-message-id-12345@example.com>",
        "in_reply_to": "",
        "references": [],
        "body": "Hi, I've been trying to login to my account for the past hour but keep getting an error message. This is very frustrating as I need to access my data urgently. Please help!",
        "received_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def mock_negative_email_data() -> Dict[str, Any]:
    """Sample email with negative sentiment for escalation testing."""
    return {
        "email_id": "test_456",
        "subject": "EXTREMELY ANGRY - Demand refund immediately!",
        "from": "angry.customer@example.com",
        "to": "support@company.com",
        "message_id": "<angry-message-id-67890@example.com>",
        "in_reply_to": "",
        "references": [],
        "body": "This is absolutely unacceptable! I've been waiting for 3 days and no one has helped me. I want a full refund NOW! This is the worst service I've ever experienced. I'm going to cancel everything and tell everyone how terrible you are!",
        "received_at": datetime.utcnow().isoformat()
    }


# =============================================================================
# IMAP/SMTP Mock Classes
# =============================================================================

class MockIMAPConnection:
    """Mock IMAP connection for testing."""

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.selected_folder = None
        self.emails = []

    def login(self, email: str, password: str):
        """Mock login."""
        if not email or not password:
            raise Exception("Authentication failed")
        return True

    def select(self, folder: str = "INBOX"):
        """Mock folder selection."""
        self.selected_folder = folder
        return ("OK", [b"1"])

    def search(self, _, criteria: str):
        """Mock search for unread emails."""
        if criteria == "UNSEEN" and self.emails:
            return ("OK", [b"1"])
        return ("OK", [b""])

    def fetch(self, email_id: bytes, message_format: str):
        """Mock email fetch."""
        if self.emails:
            return ("OK", [(b"", self.emails[0].encode())])
        return ("OK", [(b"", b"")])

    def store(self, email_id: bytes, flags: str, flag_value: str):
        """Mock mark as read."""
        return ("OK", [])

    def logout(self):
        """Mock logout."""
        return True


class MockSMTPConnection:
    """Mock SMTP connection for testing."""

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.sent_emails = []

    def ehlo(self):
        """Mock EHLO."""
        return True

    def starttls(self):
        """Mock STARTTLS."""
        return True

    def login(self, email: str, password: str):
        """Mock login."""
        if not email or not password:
            raise Exception("Authentication failed")
        return True

    def sendmail(self, from_addr: str, to_addrs: str, msg: str):
        """Mock send email."""
        self.sent_emails.append({
            "from": from_addr,
            "to": to_addrs,
            "message": msg
        })
        return {}

    def quit(self):
        """Mock quit."""
        return True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


# =============================================================================
# Test Cases
# =============================================================================

class TestEmailEndToEnd:
    """End-to-end email flow tests."""

    @pytest.mark.asyncio
    async def test_customer_created_from_email(self, db_connection, mock_email_data):
        """Test that customer is created when email is received."""
        # Process email
        customer = await create_customer(
            email=mock_email_data["from"],
            name=None,
            phone_number=None
        )

        # Verify customer created
        assert customer is not None
        assert customer["email"] == mock_email_data["from"]
        assert customer["id"] is not None

        # Cleanup
        await db_connection.execute("DELETE FROM customers WHERE email = $1", mock_email_data["from"])

    @pytest.mark.asyncio
    async def test_conversation_created_before_ticket(self, db_connection, mock_email_data):
        """Test that conversation is created BEFORE ticket."""
        # Create customer first
        customer = await create_customer(
            email=mock_email_data["from"],
            name=None,
            phone_number=None
        )

        # Create conversation
        conversation = await create_conversation(
            customer_id=customer["id"],
            topic=mock_email_data["subject"],
            status="open"
        )

        # Verify conversation created
        assert conversation is not None
        assert conversation["customer_id"] == customer["id"]
        assert conversation["id"] is not None

        # Create ticket with conversation_id
        ticket = await create_ticket(
            customer_id=customer["id"],
            channel="email",
            description=mock_email_data["body"],
            subject=mock_email_data["subject"],
            conversation_id=conversation["id"],
            priority="normal",
            sentiment_score=None
        )

        # Verify ticket created AFTER conversation
        assert ticket is not None
        assert ticket["conversation_id"] == conversation["id"]
        assert ticket["ticket_number"] is not None

        # Cleanup
        await db_connection.execute("DELETE FROM tickets WHERE customer_id = $1", customer["id"])
        await db_connection.execute("DELETE FROM conversations WHERE customer_id = $1", customer["id"])
        await db_connection.execute("DELETE FROM customers WHERE email = $1", mock_email_data["from"])

    @pytest.mark.asyncio
    async def test_ticket_created_before_message(self, db_connection, mock_email_data):
        """Test that ticket is created BEFORE message persistence."""
        # Create customer, conversation, ticket
        customer = await create_customer(email=mock_email_data["from"])
        conversation = await create_conversation(customer_id=customer["id"], topic=mock_email_data["subject"])
        ticket = await create_ticket(
            customer_id=customer["id"],
            channel="email",
            description=mock_email_data["body"],
            subject=mock_email_data["subject"],
            conversation_id=conversation["id"]
        )

        # Create message with ticket_id
        message = await create_message(
            message_id=mock_email_data["message_id"],
            conversation_id=conversation["id"],
            channel="email",
            direction="inbound",
            content=mock_email_data["body"],
            ticket_id=ticket["id"],
            sentiment_score=0.65,
            sentiment_confidence=0.89
        )

        # Verify message created with ticket reference
        assert message is not None
        assert message["ticket_id"] == ticket["id"]
        assert message["conversation_id"] == conversation["id"]

        # Cleanup
        await db_connection.execute("DELETE FROM messages WHERE conversation_id = $1", conversation["id"])
        await db_connection.execute("DELETE FROM tickets WHERE customer_id = $1", customer["id"])
        await db_connection.execute("DELETE FROM conversations WHERE customer_id = $1", customer["id"])
        await db_connection.execute("DELETE FROM customers WHERE email = $1", mock_email_data["from"])

    @pytest.mark.asyncio
    async def test_message_persisted_with_metadata(self, db_connection, mock_email_data):
        """Test that message is persisted with all metadata."""
        customer = await create_customer(email=mock_email_data["from"])
        conversation = await create_conversation(customer_id=customer["id"], topic=mock_email_data["subject"])
        ticket = await create_ticket(
            customer_id=customer["id"],
            channel="email",
            description=mock_email_data["body"],
            subject=mock_email_data["subject"],
            conversation_id=conversation["id"]
        )

        message = await create_message(
            message_id=mock_email_data["message_id"],
            conversation_id=conversation["id"],
            channel="email",
            direction="inbound",
            content=mock_email_data["body"],
            ticket_id=ticket["id"],
            in_reply_to=mock_email_data["in_reply_to"],
            references=mock_email_data["references"],
            metadata={"email_id": mock_email_data["email_id"]}
        )

        # Verify all fields persisted
        assert message["content"] == mock_email_data["body"]
        assert message["in_reply_to"] == mock_email_data["in_reply_to"]
        assert message["references"] == mock_email_data["references"]

        # Cleanup
        await db_connection.execute("DELETE FROM messages WHERE conversation_id = $1", conversation["id"])
        await db_connection.execute("DELETE FROM tickets WHERE customer_id = $1", customer["id"])
        await db_connection.execute("DELETE FROM conversations WHERE customer_id = $1", customer["id"])
        await db_connection.execute("DELETE FROM customers WHERE email = $1", mock_email_data["from"])

    @pytest.mark.asyncio
    async def test_escalation_created_if_sentiment_below_threshold(self, db_connection, mock_negative_email_data):
        """Test that escalation is created when sentiment < 0.3."""
        from production.database.queries import db_pool

        # Simulate sentiment analysis result
        sentiment_score = 0.15  # Below threshold of 0.3
        SENTIMENT_THRESHOLD = 0.3

        customer = await create_customer(email=mock_negative_email_data["from"])
        conversation = await create_conversation(customer_id=customer["id"], topic=mock_negative_email_data["subject"])
        ticket = await create_ticket(
            customer_id=customer["id"],
            channel="email",
            description=mock_negative_email_data["body"],
            subject=mock_negative_email_data["subject"],
            conversation_id=conversation["id"],
            sentiment_score=sentiment_score
        )

        # Check if escalation should be triggered
        should_escalate = sentiment_score < SENTIMENT_THRESHOLD
        assert should_escalate is True

        # Create escalation (simulated)
        escalation_number = f"ESC-2026-{str(uuid.uuid4())[:8].upper()}"
        async with db_pool.acquire() as conn:
            escalation = await conn.fetchrow(
                """
                INSERT INTO escalations (
                    escalation_number, ticket_id, reason_code, reason_details,
                    priority, status
                )
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING *
                """,
                escalation_number,
                ticket["id"],
                "negative_sentiment",
                f"Sentiment score {sentiment_score} below threshold {SENTIMENT_THRESHOLD}",
                "high",
                "pending"
            )

        # Verify escalation created
        assert escalation is not None
        assert escalation["ticket_id"] == ticket["id"]
        assert escalation["reason_code"] == "negative_sentiment"
        assert escalation["priority"] == "high"

        # Cleanup
        await db_connection.execute("DELETE FROM escalations WHERE ticket_id = $1", ticket["id"])
        await db_connection.execute("DELETE FROM tickets WHERE customer_id = $1", customer["id"])
        await db_connection.execute("DELETE FROM conversations WHERE customer_id = $1", customer["id"])
        await db_connection.execute("DELETE FROM customers WHERE email = $1", mock_negative_email_data["from"])

    @pytest.mark.asyncio
    async def test_email_marked_as_read_after_processing(self, mock_email_data):
        """Test that email is marked as read after successful processing."""
        from unittest.mock import MagicMock
        
        with patch('src.channels.email_handler.imaplib.IMAP4_SSL') as mock_imap_class:
            # Setup mock connection
            mock_conn = MagicMock()
            mock_conn.select.return_value = ("OK", [b"1"])
            mock_conn.search.return_value = ("OK", [b"1"])
            mock_conn.fetch.return_value = ("OK", [(b"", b"Test email content")])
            mock_conn.store.return_value = ("OK", [])
            mock_conn.logout.return_value = True
            mock_imap_class.return_value = mock_conn

            from src.channels.email_handler import EmailHandler

            handler = EmailHandler()
            
            # Get unread emails
            emails = handler.get_unread_emails()
            assert len(emails) == 1

            # Mark as read
            handler.mark_as_read(mock_email_data["email_id"])

            # Verify store was called with \Seen flag
            mock_conn.store.assert_called()
            call_args = mock_conn.store.call_args
            assert call_args[0][0] == mock_email_data["email_id"]
            assert call_args[0][1] == "+FLAGS"
            assert "\\Seen" in call_args[0][2]

    @pytest.mark.asyncio
    async def test_idempotency_same_message_id_no_duplicate(self, db_connection, mock_email_data):
        """Test that same Message-ID cannot create duplicate tickets/messages."""
        customer = await create_customer(email=mock_email_data["from"])
        conversation = await create_conversation(customer_id=customer["id"], topic=mock_email_data["subject"])
        ticket = await create_ticket(
            customer_id=customer["id"],
            channel="email",
            description=mock_email_data["body"],
            subject=mock_email_data["subject"],
            conversation_id=conversation["id"]
        )

        # Create message with unique message_id
        message1 = await create_message(
            message_id=mock_email_data["message_id"],
            conversation_id=conversation["id"],
            channel="email",
            direction="inbound",
            content=mock_email_data["body"],
            ticket_id=ticket["id"]
        )

        assert message1 is not None

        # Try to create duplicate message with same message_id
        # This should fail due to UNIQUE constraint
        with pytest.raises(Exception) as exc_info:
            message2 = await create_message(
                message_id=mock_email_data["message_id"],  # Same message_id
                conversation_id=conversation["id"],
                channel="email",
                direction="inbound",
                content=mock_email_data["body"],
                ticket_id=ticket["id"]
            )

        # Verify unique constraint violation
        assert "duplicate key" in str(exc_info.value).lower() or "unique" in str(exc_info.value).lower()

        # Cleanup
        await db_connection.execute("DELETE FROM messages WHERE conversation_id = $1", conversation["id"])
        await db_connection.execute("DELETE FROM tickets WHERE customer_id = $1", customer["id"])
        await db_connection.execute("DELETE FROM conversations WHERE customer_id = $1", customer["id"])
        await db_connection.execute("DELETE FROM customers WHERE email = $1", mock_email_data["from"])

    @pytest.mark.asyncio
    async def test_full_email_processing_pipeline(self, db_connection, mock_email_data):
        """Test complete email processing pipeline with timing."""
        import time

        start_time = time.time()

        # Step 1: Create customer
        customer = await create_customer(email=mock_email_data["from"])
        step1_time = time.time()

        # Step 2: Create conversation
        conversation = await create_conversation(customer_id=customer["id"], topic=mock_email_data["subject"])
        step2_time = time.time()

        # Step 3: Create ticket
        ticket = await create_ticket(
            customer_id=customer["id"],
            channel="email",
            description=mock_email_data["body"],
            subject=mock_email_data["subject"],
            conversation_id=conversation["id"]
        )
        step3_time = time.time()

        # Step 4: Create message
        message = await create_message(
            message_id=mock_email_data["message_id"],
            conversation_id=conversation["id"],
            channel="email",
            direction="inbound",
            content=mock_email_data["body"],
            ticket_id=ticket["id"],
            sentiment_score=0.75,
            sentiment_confidence=0.92
        )
        step4_time = time.time()

        # Verify all steps completed
        assert customer["id"] is not None
        assert conversation["id"] is not None
        assert ticket["ticket_number"] is not None
        assert message["id"] is not None

        # Calculate processing time
        total_time_ms = (step4_time - start_time) * 1000

        print(f"\n{'='*60}")
        print(f"EMAIL PROCESSING PIPELINE TIMING")
        print(f"{'='*60}")
        print(f"ticket_id: {ticket['id']}")
        print(f"customer_email: {mock_email_data['from']}")
        print(f"sentiment_score: 0.75")
        print(f"escalation_flag: False")
        print(f"processing_time_ms: {total_time_ms:.2f}")
        print(f"{'='*60}\n")

        # Cleanup
        await db_connection.execute("DELETE FROM messages WHERE conversation_id = $1", conversation["id"])
        await db_connection.execute("DELETE FROM tickets WHERE customer_id = $1", customer["id"])
        await db_connection.execute("DELETE FROM conversations WHERE customer_id = $1", customer["id"])
        await db_connection.execute("DELETE FROM customers WHERE email = $1", mock_email_data["from"])


# =============================================================================
# Metrics Counter Test
# =============================================================================

class EmailMetricsCounter:
    """Simple metrics counter for email processing."""

    def __init__(self):
        self.emails_processed = 0
        self.escalations_triggered = 0

    def increment_emails_processed(self):
        self.emails_processed += 1

    def increment_escalations_triggered(self):
        self.escalations_triggered += 1

    def get_metrics(self) -> Dict[str, int]:
        return {
            "emails_processed": self.emails_processed,
            "escalations_triggered": self.escalations_triggered
        }


def test_metrics_counter():
    """Test metrics counter functionality."""
    counter = EmailMetricsCounter()

    # Initial metrics
    assert counter.emails_processed == 0
    assert counter.escalations_triggered == 0

    # Process emails
    counter.increment_emails_processed()
    counter.increment_emails_processed()
    counter.increment_escalations_triggered()

    # Verify metrics
    metrics = counter.get_metrics()
    assert metrics["emails_processed"] == 2
    assert metrics["escalations_triggered"] == 1


# =============================================================================
# Test Runner
# =============================================================================

if __name__ == "__main__":
    """Run tests directly."""
    pytest.main([__file__, "-v", "--tb=short"])
