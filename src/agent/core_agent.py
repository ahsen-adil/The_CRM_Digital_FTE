"""
Core agent logic for Customer Success Digital FTE.
Handles customer inquiry processing, knowledge base search, and response generation.

This is the Stage 1 Incubation version using MCP server.
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from production.config import settings
from production.utils.logging import get_logger
from production.utils.exceptions import (
    KnowledgeBaseSearchError,
    SentimentAnalysisError,
    ResponseGenerationError
)
from production.database.repository import (
    create_customer,
    create_ticket,
    create_conversation,
    create_message,
    get_customer_by_email,
    get_active_conversation,
    get_conversation_messages,
    search_knowledge_base,
    get_customer_history
)

logger = get_logger(__name__)


class CustomerSuccessAgent:
    """
    Customer Success AI Agent for Stage 1 Incubation.
    
    Responsibilities:
    - Process incoming customer inquiries
    - Search knowledge base for relevant information
    - Generate appropriate responses
    - Determine when to escalate to human agents
    - Track conversation context across channels
    """
    
    def __init__(self):
        self.escalation_threshold = settings.SENTIMENT_THRESHOLD
        self.openai_api_key = settings.OPENAI_API_KEY
        self.openai_model = settings.OPENAI_MODEL
    
    # =========================================================================
    # Core Processing Logic
    # =========================================================================
    
    async def process_inquiry(
        self,
        from_address: str,
        subject: str,
        body: str,
        channel: str = "email",
        message_id: str = "",
        in_reply_to: Optional[str] = None,
        references: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Process a customer inquiry and generate response.
        
        Args:
            from_address: Customer email address
            subject: Message subject
            body: Message body
            channel: Communication channel (email, whatsapp, web_form)
            message_id: Unique message ID from channel
            in_reply_to: Message ID this is replying to
            references: Array of message IDs in thread
        
        Returns:
            Dictionary with response, ticket info, and escalation status
        """
        logger.info(f"Processing {channel} inquiry from {from_address}: {subject}")
        
        try:
            # Step 1: Identify or create customer
            customer = await create_customer(email=from_address)
            customer_id = customer["id"]
            logger.debug(f"Customer identified: {customer_id}")
            
            # Step 2: Find or create conversation
            conversation = await get_active_conversation(customer_id)
            if not conversation:
                # Extract topic from subject or first line
                topic = subject if subject else body[:100]
                conversation = await create_conversation(
                    customer_id=customer_id,
                    topic=topic
                )
            logger.debug(f"Conversation: {conversation['id']}")
            
            # Step 3: Analyze sentiment
            sentiment_result = await self.analyze_sentiment(body)
            sentiment_score = sentiment_result["score"]
            sentiment_confidence = sentiment_result["confidence"]
            logger.debug(f"Sentiment: {sentiment_score} (confidence: {sentiment_confidence})")
            
            # Step 4: Create message record
            message = await create_message(
                message_id=message_id or f"{channel}_{datetime.utcnow().timestamp()}",
                conversation_id=conversation["id"],
                channel=channel,
                direction="inbound",
                content=body,
                sentiment_score=sentiment_score,
                sentiment_confidence=sentiment_confidence,
                in_reply_to=in_reply_to,
                references=references
            )
            
            # Step 5: Check for escalation triggers
            escalation_check = await self.check_escalation(
                body=body,
                subject=subject,
                sentiment_score=sentiment_score
            )
            
            if escalation_check["should_escalate"]:
                logger.warning(f"Escalation triggered: {escalation_check['reason']}")
                return {
                    "response": escalation_check["response"],
                    "ticket_id": None,  # Will be created by escalation handler
                    "escalated": True,
                    "escalation_reason": escalation_check["reason"],
                    "customer": customer,
                    "conversation": conversation
                }
            
            # Step 6: Search knowledge base
            search_results = await self.search_knowledge_base(body)
            
            # Step 7: Generate response
            response = await self.generate_response(
                customer_name=customer.get("name", ""),
                subject=subject,
                body=body,
                search_results=search_results,
                channel=channel
            )
            
            # Step 8: Create ticket
            ticket = await create_ticket(
                customer_id=customer_id,
                channel=channel,
                description=body,
                subject=subject,
                conversation_id=conversation["id"],
                sentiment_score=sentiment_score
            )
            
            # Step 9: Update message with ticket_id
            # (Would need to update the message record)
            
            logger.info(f"✅ Generated response for ticket {ticket['ticket_number']}")
            
            return {
                "response": response,
                "ticket_id": ticket["id"],
                "ticket_number": ticket["ticket_number"],
                "escalated": False,
                "customer": customer,
                "conversation": conversation,
                "sentiment": sentiment_score
            }
            
        except Exception as e:
            logger.error(f"Failed to process inquiry: {e}")
            raise
    
    # =========================================================================
    # Sentiment Analysis
    # =========================================================================
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of customer message.
        
        Uses Hugging Face transformers for sentiment analysis.
        Returns score between -1.0 (negative) and 1.0 (positive).
        
        Args:
            text: Message text to analyze
        
        Returns:
            Dictionary with score (-1.0 to 1.0) and confidence (0.0 to 1.0)
        """
        try:
            # For Stage 1, use simple keyword-based sentiment
            # In production, use Hugging Face transformers
            
            negative_keywords = [
                "angry", "frustrated", "disappointed", "ridiculous", "worst",
                "terrible", "awful", "useless", "waste", "hate", "useless"
            ]
            
            positive_keywords = [
                "great", "awesome", "excellent", "love", "thank", "thanks",
                "helpful", "amazing", "wonderful", "fantastic"
            ]
            
            text_lower = text.lower()
            
            negative_count = sum(1 for word in negative_keywords if word in text_lower)
            positive_count = sum(1 for word in positive_keywords if word in text_lower)
            
            # Calculate simple sentiment score
            total = negative_count + positive_count
            if total == 0:
                score = 0.0  # Neutral
                confidence = 0.5
            else:
                score = (positive_count - negative_count) / total
                confidence = min(1.0, total / 5)  # More keywords = higher confidence
            
            logger.debug(f"Sentiment analysis: score={score}, confidence={confidence}")
            
            return {
                "score": score,
                "confidence": confidence,
                "negative_count": negative_count,
                "positive_count": positive_count
            }
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            raise SentimentAnalysisError(f"Failed to analyze sentiment: {str(e)}")
    
    # =========================================================================
    # Knowledge Base Search
    # =========================================================================
    
    async def search_knowledge_base(self, query: str) -> List[Dict[str, Any]]:
        """
        Search knowledge base for relevant information.
        
        Args:
            query: Search query text
        
        Returns:
            List of relevant articles with relevance scores
        """
        try:
            # Extract key terms from query
            # In production, use vector embeddings with pgvector
            
            results = await search_knowledge_base(query=query, limit=5)
            
            if not results:
                logger.info("No knowledge base articles found")
                return []
            
            logger.info(f"Found {len(results)} knowledge base article(s)")
            return results
            
        except Exception as e:
            logger.error(f"Knowledge base search failed: {e}")
            raise KnowledgeBaseSearchError(f"Failed to search knowledge base: {str(e)}")
    
    # =========================================================================
    # Response Generation
    # =========================================================================
    
    async def generate_response(
        self,
        customer_name: str,
        subject: str,
        body: str,
        search_results: List[Dict[str, Any]],
        channel: str = "email"
    ) -> str:
        """
        Generate response based on customer inquiry and knowledge base results.
        
        Args:
            customer_name: Customer name (for greeting)
            subject: Message subject
            body: Message body
            search_results: Relevant knowledge base articles
            channel: Communication channel (affects response style)
        
        Returns:
            Generated response text
        """
        try:
            # Use customer name or generic greeting
            name = customer_name.split()[0] if customer_name else "there"
            
            # Generate response based on channel
            if channel == "email":
                response = self._generate_email_response(
                    name=name,
                    subject=subject,
                    body=body,
                    search_results=search_results
                )
            elif channel == "whatsapp":
                response = self._generate_whatsapp_response(
                    name=name,
                    body=body,
                    search_results=search_results
                )
            else:  # web_form
                response = self._generate_web_response(
                    name=name,
                    body=body,
                    search_results=search_results
                )
            
            logger.debug(f"Generated {channel} response ({len(response)} chars)")
            return response
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            raise ResponseGenerationError(f"Failed to generate response: {str(e)}")
    
    def _generate_email_response(
        self,
        name: str,
        subject: str,
        body: str,
        search_results: List[Dict[str, Any]]
    ) -> str:
        """Generate formal email response (up to 500 words)."""
        
        greeting = f"Hi {name},"
        
        # Build response from search results
        if search_results:
            # Use most relevant article
            top_result = search_results[0]
            content = top_result.get("content", "")[:2000]  # Limit content
            
            response = f"""{greeting}

Thank you for reaching out to CloudManage support!

Regarding your question about "{subject}":

{content}

You can find more details in our documentation: https://cloudmanage.com/help

If you have any other questions, feel free to ask!

Best regards,
CloudManage Support Team
support@cloudmanage.com"""
        else:
            # No relevant articles - generic response
            response = f"""{greeting}

Thank you for reaching out to CloudManage support!

I've received your question about "{subject}" and I'm here to help.

Could you please provide a bit more detail about what you're trying to accomplish? This will help me give you the most accurate guidance.

In the meantime, you might find our help center useful: https://cloudmanage.com/help

Best regards,
CloudManage Support Team
support@cloudmanage.com"""
        
        return response
    
    def _generate_whatsapp_response(
        self,
        name: str,
        body: str,
        search_results: List[Dict[str, Any]]
    ) -> str:
        """Generate conversational WhatsApp response (160 chars preferred)."""
        
        greeting = f"Hi {name}! 👋"
        
        if search_results:
            # Extract key info from top result
            top_result = search_results[0]
            title = top_result.get("title", "")
            
            response = f"""{greeting}

Great question! About {title}:

Check our guide: https://cloudmanage.com/help/{title.replace(' ', '-').lower()}

Need more help? Just ask! 😊"""
        else:
            response = f"""{greeting}

Thanks for your message! 

Could you share a bit more detail? This helps me give you the best answer. 

In the meantime: https://cloudmanage.com/help

Chat soon! 💙"""
        
        # Trim to ~160 chars if needed
        if len(response) > 200:
            response = response[:197] + "..."
        
        return response
    
    def _generate_web_response(
        self,
        name: str,
        body: str,
        search_results: List[Dict[str, Any]]
    ) -> str:
        """Generate semi-formal web form response (up to 300 words)."""
        
        greeting = f"Hi {name},"
        
        if search_results:
            top_result = search_results[0]
            content = top_result.get("content", "")[:1000]
            
            response = f"""{greeting}

Thanks for contacting us!

Regarding your question:

{content}

For more details, visit our help center: https://cloudmanage.com/help

Best,
CloudManage Team"""
        else:
            response = f"""{greeting}

Thanks for contacting us!

I'd be happy to help with your question. To give you the best answer, could you provide a bit more detail?

Meanwhile, check out our help center: https://cloudmanage.com/help

Best,
CloudManage Team"""
        
        return response
    
    # =========================================================================
    # Escalation Detection
    # =========================================================================
    
    async def check_escalation(
        self,
        body: str,
        subject: str = "",
        sentiment_score: float = 0.0
    ) -> Dict[str, Any]:
        """
        Check if inquiry should be escalated to human agent.
        
        Escalation triggers:
        - Sentiment score < threshold (angry/frustrated customer)
        - Pricing/refund requests
        - Legal/compliance questions
        - Keywords indicating complex issue
        
        Args:
            body: Message body
            subject: Message subject
            sentiment_score: Analyzed sentiment score
        
        Returns:
            Dictionary with should_escalate flag, reason, and response
        """
        text = f"{subject} {body}".lower()
        
        # Check sentiment
        if sentiment_score < -self.escalation_threshold:
            return {
                "should_escalate": True,
                "reason": "negative_sentiment",
                "response": f"""Hi,

I'm really sorry to hear you're experiencing this issue. I understand how frustrating this must be.

I'm escalating this to our support team to ensure you get the personalized help you need. A human agent will reach out to you within 2 hours.

Your concern is important to us, and we'll make sure to resolve this for you.

Best regards,
CloudManage Support Team"""
            }
        
        # Check for pricing requests
        pricing_keywords = ["pricing", "cost", "price", "quote", "enterprise", "discount", "negotiate"]
        if any(keyword in text for keyword in pricing_keywords):
            return {
                "should_escalate": True,
                "reason": "pricing_request",
                "response": """Hi,

Thanks for your interest in CloudManage!

For pricing questions, especially for teams your size, I'd like to connect you with our sales team who can provide a custom quote.

They'll reach out within 4 hours. In the meantime, you can check out our pricing page: https://cloudmanage.com/pricing

Best regards,
CloudManage Support"""
            }
        
        # Check for refund requests
        refund_keywords = ["refund", "cancel", "chargeback", "money back", "unsubscrib"]
        if any(keyword in text for keyword in refund_keywords):
            return {
                "should_escalate": True,
                "reason": "refund_request",
                "response": """Hi,

I'm sorry to hear that you're considering canceling. I'd love to help address any concerns you have.

I'm connecting you with our billing team who can assist with refunds and cancellations. They'll reach out within 24 hours.

If there's anything specific that's not meeting your expectations, please let me know - I'm here to help!

Best regards,
CloudManage Support"""
            }
        
        # Check for legal/compliance
        legal_keywords = ["gdpr", "compliance", "legal", "privacy", "pii", "lawsuit", "lawyer", "attorney"]
        if any(keyword in text for keyword in legal_keywords):
            return {
                "should_escalate": True,
                "reason": "legal_compliance",
                "response": """Hi,

Thank you for your question regarding compliance and data privacy.

This requires specialized knowledge, so I'm escalating this to our legal/compliance team. They'll respond within 48 hours with the detailed information you need.

Best regards,
CloudManage Support"""
            }
        
        # No escalation needed
        return {
            "should_escalate": False,
            "reason": None,
            "response": None
        }


# Global agent instance
agent = CustomerSuccessAgent()


def get_agent() -> CustomerSuccessAgent:
    """Get customer success agent instance."""
    return agent
