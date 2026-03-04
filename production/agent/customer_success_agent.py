"""
Customer Success AI Agent using OpenAI Agents SDK

This agent handles customer support inquiries with:
- Context-aware responses based on company docs
- Brand voice alignment
- Automatic escalation detection
- Structured output for downstream processing
"""
from agents import Agent, Runner, function_tool
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Load context files
CONTEXT_DIR = Path(__file__).parent.parent.parent / "context"


def load_context_file(filename: str) -> str:
    """Load context from markdown file."""
    filepath = CONTEXT_DIR / filename
    if filepath.exists():
        return filepath.read_text(encoding='utf-8')
    return ""


# Load all context
COMPANY_PROFILE = load_context_file("company-profile.md")
PRODUCT_DOCS = load_context_file("product-docs.md")
BRAND_VOICE = load_context_file("brand-voice.md")
ESCALATION_RULES = load_context_file("escalation-rules.md")


# =============================================================================
# Structured Output Models
# =============================================================================

class AgentResponse(BaseModel):
    """Structured response from Customer Success Agent."""
    
    reply_text: str
    """The generated response text to send to customer."""
    
    escalation_required: bool
    """Whether this ticket requires human escalation."""
    
    escalation_reason: Optional[str] = None
    """Reason code if escalation is required."""
    
    confidence_score: float
    """Agent's confidence in the response (0.0-1.0)."""
    
    sentiment_score: float
    """Detected sentiment score (-1.0 to 1.0)."""
    
    category: str
    """Ticket category (how-to, bug, feature-request, pricing, billing, other)."""
    
    priority: str
    """Suggested priority (low, normal, high, urgent)."""


# =============================================================================
# Function Tools
# =============================================================================

@function_tool
def search_knowledge_base(query: str, category: Optional[str] = None) -> str:
    """
    Search the knowledge base for relevant information.
    
    Args:
        query: The search query from the customer.
        category: Optional category filter (pricing, features, troubleshooting, etc.).
    
    Returns:
        Relevant information from the knowledge base.
    """
    # Search product documentation
    results = []
    
    # Simple keyword search (in production, use vector search)
    query_lower = query.lower()
    
    if "project" in query_lower and "create" in query_lower:
        results.append(PRODUCT_DOCS.split("## Getting Started")[1].split("##")[0])
    
    if "pricing" in query_lower or "cost" in query_lower or "plan" in query_lower:
        pricing_section = PRODUCT_DOCS.split("## Pricing Plans")[1].split("##")[0]
        results.append(f"PRICING INFO:\n{pricing_section}")
    
    if "invite" in query_lower or "team" in query_lower:
        results.append("To invite team members: Go to Settings > Team > Invite Members, enter email addresses, and send invitations.")
    
    if "export" in query_lower or "download" in query_lower:
        results.append("To export data: Go to Settings > Export Data to download all your projects, tasks, and time entries in CSV/Excel format.")
    
    if "login" in query_lower or "sign in" in query_lower:
        results.append("Login issues: Try resetting password at https://cloudmanage.com/reset-password. Check if email is verified. Contact support if issue persists.")
    
    if "file" in query_lower and ("upload" in query_lower or "size" in query_lower):
        results.append("File upload limits: 100MB per file on Pro plan, 1GB on Enterprise. Supported formats: PDF, DOC, DOCX, XLS, XLSX, PNG, JPG, GIF, MP4.")
    
    # If no specific match, return general info
    if not results:
        results.append("CloudManage is a project management platform with features for: project management, team collaboration, time tracking, reporting, and integrations.")
    
    return "\n\n".join(results)


@function_tool
def check_escalation_criteria(
    sentiment_score: float,
    message_content: str,
    category: str
) -> str:
    """
    Check if escalation criteria are met based on rules.
    
    Args:
        sentiment_score: The detected sentiment score.
        message_content: The customer's message content.
        category: The ticket category.
    
    Returns:
        Escalation recommendation with reason code.
    """
    content_lower = message_content.lower()
    
    # Check sentiment threshold
    if sentiment_score < 0.3:
        return "ESCALATION_RECOMMENDED: negative_sentiment - Customer shows negative sentiment"
    
    # Check pricing keywords
    pricing_keywords = ["pricing", "cost", "quote", "enterprise", "discount", "negotiate", "custom pricing"]
    if any(kw in content_lower for kw in pricing_keywords):
        return "ESCALATION_RECOMMENDED: pricing_request - Pricing inquiry detected"
    
    # Check refund keywords
    refund_keywords = ["refund", "cancel", "chargeback", "money back", "billing issue", "overcharged"]
    if any(kw in content_lower for kw in refund_keywords):
        return "ESCALATION_RECOMMENDED: refund_request - Refund request detected"
    
    # Check legal keywords
    legal_keywords = ["gdpr", "compliance", "legal", "lawsuit", "lawyer", "data privacy", "terms of service"]
    if any(kw in content_lower for kw in legal_keywords):
        return "ESCALATION_RECOMMENDED: legal_compliance - Legal/compliance issue detected"
    
    # Check for human agent request
    human_keywords = ["speak to human", "real person", "agent", "not talking to bot"]
    if any(kw in content_lower for kw in human_keywords):
        return "ESCALATION_RECOMMENDED: customer_request - Customer requested human agent"
    
    return "NO_ESCALATION - Can be handled by AI agent"


# =============================================================================
# Customer Success Agent Definition
# =============================================================================

customer_success_agent = Agent(
    name="CustomerSuccessAgent",
    instructions=f"""You are a Customer Success AI Agent for CloudManage, a project management SaaS platform.

## Your Role
- Respond to customer support inquiries via email
- Provide helpful, accurate information based on company documentation
- Maintain brand voice and tone
- Detect when escalation to human agents is needed

## Company Context
{COMPANY_PROFILE}

## Product Documentation
{PRODUCT_DOCS}

## Brand Voice Guidelines
{BRAND_VOICE}

## Escalation Rules
{ESCALATION_RULES}

## Response Guidelines

1. **Tone**: Friendly, helpful, professional. Use contractions (we're, you'll, let's).
2. **Structure**: 
   - Start with warm greeting
   - Acknowledge customer's question/issue
   - Provide clear, actionable answer
   - End with offer for further help
3. **Length**: Keep responses concise but complete (100-300 words for email)
4. **Accuracy**: Only provide information found in documentation
5. **Escalation**: Recommend escalation when:
   - Sentiment is negative (< 0.3)
   - Pricing/billing/refund requests
   - Legal/compliance questions
   - Issue beyond your knowledge

## Output Requirements

You MUST return a structured response with:
- reply_text: Your complete response to the customer
- escalation_required: true/false
- escalation_reason: Reason code if escalation needed
- confidence_score: Your confidence (0.0-1.0)
- sentiment_score: Detected sentiment (-1.0 to 1.0)
- category: Ticket category
- priority: Suggested priority

Be empathetic, solution-oriented, and always maintain professionalism.
""",
    tools=[search_knowledge_base, check_escalation_criteria],
    output_type=AgentResponse,
    model="gpt-4o",
)


# =============================================================================
# Agent Runner Interface
# =============================================================================

async def process_customer_inquiry(
    customer_email: str,
    subject: str,
    message_body: str,
    previous_messages: Optional[List[str]] = None
) -> AgentResponse:
    """
    Process a customer support inquiry using the AI agent.
    
    Args:
        customer_email: Customer's email address
        subject: Email subject line
        message_body: Customer's message content
        previous_messages: Optional list of previous messages in conversation
    
    Returns:
        AgentResponse with reply text and metadata
    """
    # Build conversation context
    context = {
        "customer_email": customer_email,
        "subject": subject,
    }
    
    # Build input prompt
    input_prompt = f"""Customer Email:
From: {customer_email}
Subject: {subject}

Message:
{message_body}

{"Previous Messages:\n" + "\n".join(previous_messages) if previous_messages else ""}

Please provide a helpful response following the brand voice guidelines."""

    # Run the agent
    result = await Runner.run(
        customer_success_agent,
        input_prompt,
        context=context
    )
    
    # Parse and return structured output
    response = result.final_output_as(AgentResponse)
    return response


def run_agent_sync(
    customer_email: str,
    subject: str,
    message_body: str,
    previous_messages: Optional[List[str]] = None
) -> AgentResponse:
    """
    Synchronous wrapper for process_customer_inquiry.
    
    Use this when calling from synchronous code (like email polling).
    """
    return asyncio.run(process_customer_inquiry(
        customer_email=customer_email,
        subject=subject,
        message_body=message_body,
        previous_messages=previous_messages
    ))


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    # Test the agent
    test_email = {
        "customer_email": "john@example.com",
        "subject": "How do I create my first project?",
        "message_body": """Hi,

I just signed up for CloudManage and I'm excited to get started. Can you help me understand how to create my first project?

Thanks,
John"""
    }
    
    print("Testing Customer Success Agent...")
    print("=" * 60)
    
    response = run_agent_sync(
        customer_email=test_email["customer_email"],
        subject=test_email["subject"],
        message_body=test_email["message_body"]
    )
    
    print(f"\nReply Text:\n{response.reply_text}")
    print(f"\nEscalation Required: {response.escalation_required}")
    print(f"Escalation Reason: {response.escalation_reason}")
    print(f"Confidence Score: {response.confidence_score}")
    print(f"Sentiment Score: {response.sentiment_score}")
    print(f"Category: {response.category}")
    print(f"Priority: {response.priority}")
    print("=" * 60)
