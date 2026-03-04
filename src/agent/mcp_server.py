"""
MCP Server for Customer Success Digital FTE - Stage 1 Incubation.

Exposes agent capabilities as MCP tools:
- search_knowledge_base
- create_ticket
- get_customer_history
- send_response
- escalate_to_human

This allows Qwen Coder to interact with the agent during the incubation phase.
"""
import asyncio
import logging
from typing import Optional, Dict, Any, List

from mcp.server import Server
from mcp.types import Tool, TextContent

from production.config import settings
from production.utils.logging import get_logger, setup_logging
from src.agent.core_agent import CustomerSuccessAgent
from production.database.repository import (
    create_ticket,
    get_customer_history,
    search_knowledge_base as repo_search_kb
)
from src.channels.email_handler import EmailHandler

logger = get_logger(__name__)

# Initialize server
server = Server("customer-success-fte")

# Initialize components
agent = CustomerSuccessAgent()
email_handler = EmailHandler()


# =============================================================================
# MCP Tools
# =============================================================================

@server.tool("search_knowledge_base")
async def search_knowledge_base(query: str, limit: int = 5) -> str:
    """
    Search product documentation for relevant information.
    
    Use this when the customer asks questions about product features,
    how to use something, or needs technical information.
    
    Args:
        query: Search query text
        limit: Maximum results to return (default: 5)
    
    Returns:
        Formatted search results with relevance scores
    """
    try:
        results = await repo_search_kb(query=query, limit=limit)
        
        if not results:
            return "No relevant documentation found. Consider escalating to human support."
        
        # Format results
        formatted = []
        for r in results:
            formatted.append(
                f"**{r['title']}** (relevance: {r.get('relevance', 'N/A')})\n"
                f"{r['content'][:500]}..."  # Truncate long content
            )
        
        return "\n\n---\n\n".join(formatted)
        
    except Exception as e:
        logger.error(f"Knowledge base search failed: {e}")
        return f"Knowledge base search failed: {str(e)}. Consider escalating."


@server.tool("create_ticket")
async def create_ticket_tool(
    customer_email: str,
    channel: str,
    description: str,
    subject: Optional[str] = None,
    priority: str = "normal"
) -> str:
    """
    Create a support ticket in the system with channel tracking.
    
    Required for all customer interactions. Creates a ticket record
    that tracks the inquiry through resolution.
    
    Args:
        customer_email: Customer email address (used as primary identifier)
        channel: Origin channel (email, whatsapp, web_form)
        description: Customer's issue or question
        subject: Optional subject line
        priority: Ticket priority (low, normal, high, urgent)
    
    Returns:
        Ticket number (e.g., "TKT-2026-000123")
    """
    try:
        # First, ensure customer exists
        from production.database.repository import create_customer
        customer = await create_customer(email=customer_email)
        
        # Create ticket
        ticket = await create_ticket(
            customer_id=customer["id"],
            channel=channel,
            description=description,
            subject=subject,
            priority=priority
        )
        
        logger.info(f"Created ticket {ticket['ticket_number']} for {customer_email}")
        return ticket["ticket_number"]
        
    except Exception as e:
        logger.error(f"Failed to create ticket: {e}")
        return f"ERROR: Failed to create ticket: {str(e)}"


@server.tool("get_customer_history")
async def get_customer_history_tool(customer_email: str) -> str:
    """
    Get customer's interaction history across ALL channels.
    
    Use this to understand the customer's context before responding.
    Shows previous tickets, conversations, and sentiment trends.
    
    Args:
        customer_email: Customer email address
    
    Returns:
        Formatted customer history including tickets, conversations, and sentiment
    """
    try:
        from production.database.repository import get_customer_by_email
        customer = await get_customer_by_email(customer_email)
        
        if not customer:
            return f"No customer found with email: {customer_email}"
        
        history = await get_customer_history(customer["id"])
        
        # Format history
        output = [f"**Customer**: {customer.get('name', 'N/A')} ({customer_email})"]
        output.append(f"**Total Tickets**: {history['total_tickets']}")
        output.append(f"**Average Sentiment**: {history['average_sentiment'] or 'N/A'}")
        output.append("")
        
        # Recent tickets
        if history["tickets"]:
            output.append("**Recent Tickets**:")
            for ticket in history["tickets"][:5]:
                output.append(
                    f"- {ticket['ticket_number']}: {ticket['subject'] or 'No subject'} "
                    f"({ticket['status']})"
                )
        else:
            output.append("**No previous tickets**")
        
        return "\n".join(output)
        
    except Exception as e:
        logger.error(f"Failed to get customer history: {e}")
        return f"ERROR: Failed to get customer history: {str(e)}"


@server.tool("send_response")
async def send_response_tool(
    customer_email: str,
    subject: str,
    body: str,
    channel: str = "email",
    in_reply_to: Optional[str] = None,
    references: Optional[List[str]] = None
) -> str:
    """
    Send response via the appropriate channel.
    
    Formats and sends the response using channel-appropriate styling:
    - Email: Formal, detailed (up to 500 words)
    - WhatsApp: Conversational, concise (160 chars)
    - Web: Semi-formal (up to 300 words)
    
    Args:
        customer_email: Customer email address
        subject: Response subject
        body: Response body content
        channel: Communication channel (email, whatsapp, web_form)
        in_reply_to: Message ID for threading (email only)
        references: Reference headers for threading (email only)
    
    Returns:
        Delivery status message
    """
    try:
        if channel == "email":
            # Send via SMTP
            email_handler.send_new_email(
                to=customer_email,
                subject=subject,
                body=body
            )
            return f"✅ Email response sent to {customer_email}"
            
        elif channel == "whatsapp":
            # Send via Whapi (would be implemented in Stage 2)
            logger.info(f"WhatsApp response prepared for {customer_email}: {body[:100]}")
            return f"✅ WhatsApp response prepared for {customer_email}"
            
        else:  # web_form
            # Web form responses are typically shown on screen + email confirmation
            email_handler.send_new_email(
                to=customer_email,
                subject=f"Re: {subject}",
                body=body
            )
            return f"✅ Web form response sent to {customer_email}"
            
    except Exception as e:
        logger.error(f"Failed to send response: {e}")
        return f"ERROR: Failed to send response: {str(e)}"


@server.tool("escalate_to_human")
async def escalate_to_human_tool(
    ticket_id: str,
    reason: str,
    reason_details: str,
    assigned_team: Optional[str] = None
) -> str:
    """
    Hand off complex issues to human support with full context.
    
    Use this when:
    - Customer sentiment is negative (< 0.3)
    - Pricing/refund requests
    - Legal/compliance questions
    - Complex technical issues beyond documentation
    
    Args:
        ticket_id: Ticket ID to escalate
        reason: Reason code (negative_sentiment, pricing_request, refund_request,
                legal_compliance, complex_issue, knowledge_gap, customer_request)
        reason_details: Detailed explanation of why escalation is needed
        assigned_team: Optional team assignment (sales, billing, support, legal)
    
    Returns:
        Escalation confirmation with escalation number
    """
    try:
        # In Stage 1, log the escalation
        # In Stage 2, create escalation record in database
        
        escalation_number = f"ESC-{asyncio.get_event_loop().time():.0f}"
        
        logger.warning(
            f"🚨 ESCALATION {escalation_number}: Ticket {ticket_id} - {reason}",
            extra={
                "ticket_id": ticket_id,
                "escalation_reason": reason,
                "assigned_team": assigned_team
            }
        )
        
        # Send notification email to assigned team
        team_email = {
            "sales": "sales@cloudmanage.com",
            "billing": "billing@cloudmanage.com",
            "support": "support-team@cloudmanage.com",
            "legal": "legal@cloudmanage.com"
        }.get(assigned_team or "support", "support-team@cloudmanage.com")
        
        notification_body = f"""
ESCALATION NOTIFICATION

Escalation Number: {escalation_number}
Ticket ID: {ticket_id}
Reason: {reason}
Details: {reason_details}
Assigned Team: {assigned_team or "Support"}

Please review and respond to the customer within SLA.

--
CloudManage Support System"""
        
        email_handler.send_new_email(
            to=team_email,
            subject=f"🚨 Escalation {escalation_number} - Ticket {ticket_id}",
            body=notification_body
        )
        
        return (
            f"✅ Escalation {escalation_number} created for ticket {ticket_id}. "
            f"Notification sent to {assigned_team or 'support'} team."
        )
        
    except Exception as e:
        logger.error(f"Failed to escalate: {e}")
        return f"ERROR: Failed to escalate: {str(e)}"


# =============================================================================
# Server Entry Point
# =============================================================================

if __name__ == "__main__":
    # Setup logging
    setup_logging(level=settings.LOG_LEVEL, environment=settings.ENVIRONMENT)
    
    logger.info("🚀 Starting Customer Success FTE MCP Server...")
    logger.info(f"Email: {settings.EMAIL_ADDRESS}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    # Run the server
    import asyncio
    from mcp.server.stdio import stdio_server
    
    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    
    asyncio.run(main())
