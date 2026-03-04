"""
WhatsApp Webhook Server with Kafka Integration

Production-ready WhatsApp webhook handler with:
- Kafka event production for incoming messages
- AI agent processing
- WhatsApp reply sending
- Full logging and error handling
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import time
import json
import logging
import asyncio  # Added for AI agent
import concurrent.futures  # Added for thread executor
from production.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="WhatsApp Webhook API", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Kafka producer
kafka_producer = None
try:
    from production.utils.kafka_producer import init_kafka_producer
    kafka_producer = init_kafka_producer(settings.KAFKA_BOOTSTRAP_SERVERS)
    logger.info('Kafka producer initialized for WhatsApp')
except Exception as e:
    logger.warning(f'Kafka producer initialization failed: {e}. Running without Kafka.')

# Processed messages tracking
processed_messages = set()
MAX_STORED_IDS = 10000


# =============================================================================
# Database Functions
# =============================================================================

def get_db_conn():
    return psycopg2.connect(settings.DATABASE_URL, sslmode='require')


def create_customer_whatsapp(phone_number: str, name: str):
    """Create or find customer by WhatsApp number"""
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM customers WHERE phone_number = %s", (phone_number,))
            customer = cur.fetchone()
            
            if not customer:
                cur.execute(
                    "INSERT INTO customers (phone_number, name, preferred_channel) VALUES (%s, %s, 'whatsapp') RETURNING *",
                    (phone_number, name)
                )
                customer = cur.fetchone()
                conn.commit()
                return dict(customer), True
            
            conn.close()
            return dict(customer), False
    finally:
        conn.close()


def create_conversation(customer_id: str, topic: str):
    """Create conversation"""
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO conversations (customer_id, topic, status) VALUES (%s, %s, 'open') RETURNING *",
                (customer_id, topic)
            )
            conversation = cur.fetchone()
            conn.commit()
            return dict(conversation)
    finally:
        conn.close()


def create_ticket(customer_id: str, channel: str, description: str, conversation_id: str):
    """Create ticket"""
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO tickets (customer_id, channel, description, conversation_id, status, priority)
                VALUES (%s, %s, %s, %s, 'open', 'normal') RETURNING *
                """,
                (customer_id, channel, description, conversation_id)
            )
            ticket = cur.fetchone()
            conn.commit()
            return dict(ticket)
    finally:
        conn.close()


# =============================================================================
# AI Agent (ACTUAL OPENAI AGENT)
# =============================================================================

def run_ai_agent_sync(customer_email: str, subject: str, message_body: str) -> Dict[str, Any]:
    """Generate AI response using ACTUAL OpenAI Agent - THREAD SAFE"""
    logger.info("="*80)
    logger.info("CALLING OPENAI AGENT FOR WHATSAPP")
    logger.info("="*80)
    logger.info(f"Customer: {customer_email}")
    logger.info(f"Subject: {subject}")
    logger.info(f"Message: {message_body[:100]}...")
    
    try:
        logger.info("Calling AI agent for WhatsApp...")
        from production.agent.customer_success_agent import process_customer_inquiry
        import concurrent.futures
        
        logger.info("Import successful")
        logger.info("Calling OpenAI Agent in thread executor (to avoid event loop conflict)...")
        
        # Run AI agent in thread executor to avoid event loop conflict
        # This is necessary because FastAPI runs on an async event loop
        # and we can't call asyncio.run() from within it
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                lambda: asyncio.run(process_customer_inquiry(
                    customer_email=customer_email,
                    subject=subject,
                    message_body=message_body
                ))
            )
            ai_response = future.result(timeout=60)  # 60 second timeout
        
        logger.info("="*80)
        logger.info("✅ AGENT RESPONSE GENERATED")
        logger.info("="*80)
        logger.info(f"Reply Text: {ai_response.reply_text[:200]}...")
        logger.info(f"Sentiment: {ai_response.sentiment_score}")
        logger.info(f"Confidence: {ai_response.confidence_score}")
        logger.info(f"Escalation: {ai_response.escalation_required}")
        logger.info(f"Category: {ai_response.category}")
        logger.info("="*80)

        return {
            "reply_text": ai_response.reply_text,
            "sentiment_score": ai_response.sentiment_score,
            "confidence_score": ai_response.confidence_score,
            "escalation_required": ai_response.escalation_required,
            "escalation_reason": ai_response.escalation_reason or "",
            "category": ai_response.category,
            "priority": ai_response.priority
        }

    except concurrent.futures.TimeoutError as e:
        logger.error("="*80)
        logger.error("❌ FALLBACK TRIGGERED")
        logger.error("="*80)
        logger.error(f"Fallback reason: TimeoutError")
        logger.error(f"Error message: AI agent took too long to respond (>60s)")
        logger.error("="*80)
        
        return {
            "reply_text": f"Thank you for contacting us. We received your message: '{message_body[:100]}...'. We'll respond shortly.",
            "sentiment_score": 0.75,
            "confidence_score": 0.0,
            "escalation_required": False,
            "escalation_reason": "",
            "category": "general",
            "priority": "normal"
        }
        
    except Exception as e:
        logger.error("="*80)
        logger.error("❌ FALLBACK TRIGGERED")
        logger.error("="*80)
        logger.error(f"Fallback reason: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error("Full traceback:")
        import traceback
        logger.error(traceback.format_exc())
        logger.error("="*80)
        logger.error("USING STATIC FALLBACK RESPONSE")
        logger.error("="*80)
        
        # Fallback response
        return {
            "reply_text": f"Thank you for contacting us. We received your message: '{message_body[:100]}...'. We'll respond shortly.",
            "sentiment_score": 0.75,
            "confidence_score": 0.0,
            "escalation_required": False,
            "escalation_reason": "",
            "category": "general",
            "priority": "normal"
        }


# =============================================================================
# WhatsApp Handler
# =============================================================================

class WhatsAppHandler:
    """WhatsApp message sender using Whapi.Cloud API"""
    
    def __init__(self):
        self.api_key = settings.WHAPI_API_KEY
        self.phone_id = settings.WHAPI_PHONE_ID
        self.base_url = settings.WHAPI_BASE_URL or "https://gate.whapi.cloud"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def send_reply(self, message_data: Dict[str, Any], reply_text: str) -> bool:
        """Send WhatsApp reply via Whapi.Cloud API"""
        try:
            # Get phone number from chat_id or from field
            chat_id = message_data.get('chat_id', '')
            phone_number = chat_id.split('@')[0] if '@' in chat_id else message_data.get('from', '')
            
            logger.info(f"Sending WhatsApp to {phone_number} via Whapi API")
            
            # Whapi.Cloud API endpoint
            url = f"{self.base_url}/messages/text"
            
            # Prepare payload
            payload = {
                "to": phone_number,
                "body": reply_text
            }
            
            # Make API call
            import requests
            response = requests.post(url, json=payload, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                message_id = result.get('message_id', 'N/A')
                logger.info(f"WhatsApp sent successfully via Whapi: {message_id}")
                return True
            else:
                logger.error(f"Whapi API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send WhatsApp via Whapi: {e}")
            return False


# =============================================================================
# Webhook Endpoint
# =============================================================================

@app.post("/whatsapp-webhook")
@app.post("/whatsapp-webhook/messages")
@app.post("/messages")
async def whatsapp_webhook(request: Request):
    """
    Receive WhatsApp messages from Whapi.Cloud
    Produces Kafka events for event-driven processing
    """
    try:
        data = await request.json()
        logger.info(f"Received WhatsApp webhook: {json.dumps(data, indent=2)}")
        
        messages = data.get('messages', [])
        
        if not messages:
            return JSONResponse(content={"status": "ok", "message": "No messages"})
        
        processed_count = 0
        
        for msg in messages:
            # Skip if from ourselves
            if msg.get('from_me', True):
                continue
            
            # Skip if not text
            if msg.get('type') != 'text':
                continue
            
            # Skip if already processed
            message_id = msg.get('id', '')
            if message_id in processed_messages:
                logger.info(f"Skipping already processed message: {message_id}")
                continue
            
            # Process message
            phone_number = msg['from'].split('@')[0]
            customer_name = msg.get('from_name', 'WhatsApp User')
            message_body = msg.get('text', {}).get('body', '')
            
            logger.info(f"Processing WhatsApp from {phone_number}: {message_body[:50]}...")
            
            # Create customer
            customer, is_new = create_customer_whatsapp(phone_number, customer_name)
            customer_id = customer['id']
            logger.info(f"Customer: {customer_id} ({'new' if is_new else 'existing'})")
            
            # Create conversation
            conversation = create_conversation(customer_id, "WhatsApp Support")
            conversation_id = conversation['id']
            logger.info(f"Conversation: {conversation_id}")
            
            # Create ticket
            ticket = create_ticket(customer_id, 'whatsapp', message_body, conversation_id)
            ticket_id = ticket['id']
            ticket_number = ticket['ticket_number']
            logger.info(f"Ticket: {ticket_number}")
            
            # Produce Kafka event
            if kafka_producer:
                try:
                    kafka_producer.produce_ticket_event(
                        event_type='whatsapp_received',
                        ticket_id=ticket_id,
                        customer_id=customer_id,
                        channel='whatsapp',
                        subject='WhatsApp Message',
                        message=message_body[:500],
                        metadata={
                            'message_id': message_id,
                            'from': phone_number,
                            'chat_id': msg.get('chat_id', ''),
                        }
                    )
                    logger.info(f"Kafka event produced for WhatsApp: {message_id}")
                except Exception as e:
                    logger.warning(f"Failed to produce Kafka event: {e}")
            
            # Generate AI response
            logger.info("="*60)
            logger.info("GENERATING AI RESPONSE")
            logger.info("="*60)
            ai_response = run_ai_agent_sync(f"{phone_number}@whatsapp.com", "WhatsApp Support", message_body)
            logger.info(f"AI response generated: sentiment={ai_response['sentiment_score']}")
            logger.info(f"Reply text type: {type(ai_response['reply_text'])}")
            logger.info(f"Reply text length: {len(ai_response['reply_text'])}")
            logger.info(f"Reply text preview: {ai_response['reply_text'][:100]}...")
            logger.info("="*60)

            # Send WhatsApp reply
            logger.info("Preparing to send WhatsApp reply...")
            handler = WhatsAppHandler()
            # Encode to avoid Unicode issues, limit to 500 chars
            reply_text = ai_response['reply_text'].encode('utf-8', errors='ignore').decode('utf-8')[:500]
            logger.info(f"Reply text to send ({len(reply_text)} chars): {reply_text[:100]}...")
            logger.info("Calling handler.send_reply()...")
            success = handler.send_reply(msg, reply_text)
            logger.info(f"WhatsApp reply sent: {success}")
            logger.info("="*60)
            
            # Mark as processed
            processed_messages.add(message_id)
            processed_count += 1
        
        # Cleanup old IDs
        if len(processed_messages) > MAX_STORED_IDS:
            to_remove = list(processed_messages)[:MAX_STORED_IDS // 10]
            for id in to_remove:
                processed_messages.discard(id)
            logger.info(f"Cleaned up {len(to_remove)} old message IDs")
        
        return JSONResponse(
            content={
                "status": "ok",
                "processed": processed_count,
                "messages_received": len(messages)
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": "WhatsApp Webhook API",
        "kafka": "connected" if kafka_producer else "disconnected",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "WhatsApp Webhook API",
        "version": "2.0.0",
        "kafka_integration": True,
        "endpoints": {
            "webhook": "POST /whatsapp-webhook",
            "health": "GET /health"
        }
    }


if __name__ == "__main__":
    import uvicorn

    logger.info("="*80)
    logger.info("WHATSAPP WEBHOOK API v2.0.0 - WITH KAFKA")
    logger.info("="*80)
    logger.info("Running on http://localhost:8000")
    logger.info("="*80)
    
    # Test AI agent import on startup
    logger.info("Testing AI agent import...")
    try:
        from production.agent.customer_success_agent import run_agent_sync
        logger.info("✅ AI agent module imported successfully")
        
        # Test with a simple call
        logger.info("Testing AI agent with sample call...")
        test_response = run_agent_sync(
            customer_email="test@whatsapp.com",
            subject="Test",
            message_body="Hello"
        )
        logger.info(f"✅ AI agent test successful!")
        logger.info(f"   Reply preview: {test_response.reply_text[:50]}...")
        logger.info(f"   Sentiment: {test_response.sentiment_score}")
        logger.info(f"   Confidence: {test_response.confidence_score}")
    except Exception as e:
        logger.error("="*80)
        logger.error("❌ AI AGENT IMPORT/TEST FAILED")
        logger.error("="*80)
        logger.error(f"Error: {type(e).__name__}: {e}")
        logger.error("WhatsApp will use FALLBACK responses until this is fixed!")
        logger.error("="*80)
        import traceback
        logger.error(traceback.format_exc())
    
    logger.info("="*80)
    logger.info("Starting WhatsApp Webhook server...")
    logger.info("="*80)

    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1)
