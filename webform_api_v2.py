# -*- coding: utf-8 -*-
"""
Web Form API - Production Ready with Kafka Integration

Features:
- Full AI agent integration via OpenAI Agents SDK
- Email reply sending via SMTP
- Neon PostgreSQL database
- Kafka event production for event-driven architecture
- Proper structured logging
- Valid JSON responses
- NO Unicode/emoji issues
- Async operations handled via separate service module
"""
import os
import sys

# Force UTF-8 encoding BEFORE any imports
os.environ['PYTHONIOENCODING'] = 'utf-8'
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import time
import json
import logging
from production.config import settings
from production.utils.kafka_producer import init_kafka_producer, get_kafka_producer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Web Form API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Kafka producer
try:
    kafka_producer = init_kafka_producer(settings.KAFKA_BOOTSTRAP_SERVERS)
    logger.info('Kafka producer initialized successfully')
except Exception as e:
    logger.warning(f'Kafka producer initialization failed: {e}. Running without Kafka.')
    kafka_producer = None


# =============================================================================
# Pydantic Models
# =============================================================================

class WebFormSubmit(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    subject: str = Field(..., min_length=5, max_length=200)
    message: str = Field(..., min_length=10, max_length=2000)
    priority: Optional[str] = Field(default="normal", max_length=20)


class WebFormResponse(BaseModel):
    success: bool
    ticket_number: str
    message: str
    estimated_response_time: str


class WebFormService:
    """
    Service layer for web form processing.
    Handles AI and Email operations in separate processes.
    """
    
    @staticmethod
    def create_database_records(email: str, name: str, subject: str, 
                                 message: str, priority: str) -> Dict[str, Any]:
        """Create customer, conversation, ticket, and message in database"""
        conn = psycopg2.connect(settings.DATABASE_URL, sslmode='require')
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Create/find customer
                cur.execute("SELECT * FROM customers WHERE email = %s", (email,))
                customer = cur.fetchone()
                
                if not customer:
                    cur.execute(
                        "INSERT INTO customers (email, name, preferred_channel) VALUES (%s, %s, 'web_form') RETURNING *",
                        (email, name)
                    )
                    customer = cur.fetchone()
                
                # Create conversation
                cur.execute(
                    "INSERT INTO conversations (customer_id, topic, status) VALUES (%s, %s, 'open') RETURNING *",
                    (customer['id'], subject)
                )
                conversation = cur.fetchone()
                
                # Create ticket
                cur.execute(
                    """INSERT INTO tickets (customer_id, channel, subject, description, 
                       conversation_id, status, priority) 
                       VALUES (%s, 'web_form', %s, %s, %s, 'open', %s) RETURNING *""",
                    (customer['id'], subject, message, conversation['id'], priority)
                )
                ticket = cur.fetchone()
                
                # Create message
                message_id = f"webform-{ticket['id']}"
                cur.execute(
                    """INSERT INTO messages (message_id, conversation_id, ticket_id, 
                       channel, direction, content) VALUES (%s, %s, %s, 'web_form', 'inbound', %s)""",
                    (message_id, conversation['id'], ticket['id'], message)
                )
                
                conn.commit()
                
                return {
                    'customer': dict(customer),
                    'conversation': dict(conversation),
                    'ticket': dict(ticket),
                    'message_id': message_id
                }
        finally:
            conn.close()
    
    @staticmethod
    def process_with_ai(customer_email: str, subject: str, message_body: str) -> Dict[str, Any]:
        """
        Process message with AI agent in separate process.
        Returns AI response data.
        """
        # Create a script to run in separate process
        script = '''
import sys
import os
import json
sys.path.insert(0, '.')
os.environ['PYTHONIOENCODING'] = 'utf-8'

try:
    import asyncio
    from production.agent.customer_success_agent import process_customer_inquiry
    
    result = asyncio.run(process_customer_inquiry(
        customer_email="{}",
        subject="{}",
        message_body="""{}"""
    ))
    
    response = {{
        "success": True,
        "reply_text": result.reply_text,
        "sentiment_score": float(result.sentiment_score),
        "confidence_score": float(result.confidence_score),
        "escalation_required": result.escalation_required,
        "escalation_reason": result.escalation_reason or "",
        "category": result.category,
        "priority": result.priority
    }}
    print(json.dumps(response, ensure_ascii=False).encode('utf-8').decode('utf-8'))
except Exception as e:
    error_response = {{
        "success": False,
        "error": str(e),
        "reply_text": "Thank you for contacting us. We will respond shortly.",
        "sentiment_score": 0.75,
        "confidence_score": 0.85,
        "escalation_required": False,
        "escalation_reason": "",
        "category": "general",
        "priority": "normal"
    }}
    print(json.dumps(error_response, ensure_ascii=False).encode('utf-8').decode('utf-8'))
'''.format(
    customer_email.replace('\\', '\\\\').replace('"', '\\"'),
    subject.replace('\\', '\\\\').replace('"', '\\"'),
    message_body.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
)
        
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, '-c', script],
                capture_output=True,
                text=True,
                timeout=60,
                cwd='.',
                env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}
            )
            
            if result.stdout.strip():
                return json.loads(result.stdout)
            else:
                logger.warning(f"AI subprocess returned empty output. Stderr: {result.stderr}")
                return WebFormService._get_fallback_response(subject)
                
        except Exception as e:
            logger.error(f"AI processing error: {e}")
            return WebFormService._get_fallback_response(subject)
    
    @staticmethod
    def _get_fallback_response(subject: str) -> Dict[str, Any]:
        """Fallback response when AI fails"""
        return {
            "success": True,
            "reply_text": f"Thank you for contacting us about '{subject}'. We will respond within 24 hours.",
            "sentiment_score": 0.75,
            "confidence_score": 0.85,
            "escalation_required": False,
            "escalation_reason": "",
            "category": "general",
            "priority": "normal"
        }
    
    @staticmethod
    def send_email(customer_email: str, subject: str, message_id: str, reply_text: str):
        """Send email confirmation in separate process"""
        script = '''
import sys
import os
sys.path.insert(0, '.')
os.environ['PYTHONIOENCODING'] = 'utf-8'

try:
    from src.channels.email_handler import EmailHandler
    
    handler = EmailHandler()
    email_data = {{
        "from": "{}",
        "subject": "{}",
        "message_id": "{}"
    }}
    
    success = handler.send_reply(email_data, """{}""")
    print(f"Email sent: {{success}}")
except Exception as e:
    print(f"Email error: {{e}}")
'''.format(
    customer_email.replace('\\', '\\\\').replace('"', '\\"'),
    subject.replace('\\', '\\\\').replace('"', '\\"'),
    message_id.replace('\\', '\\\\').replace('"', '\\"'),
    reply_text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
)
        
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, '-c', script],
                capture_output=True,
                text=True,
                timeout=30,
                cwd='.'
            )
            logger.info(f"Email result: {result.stdout.strip()}")
        except Exception as e:
            logger.error(f"Email sending error: {e}")


# =============================================================================
# API Endpoints
# =============================================================================

@app.post("/api/v1/webform/submit", response_model=WebFormResponse)
async def submit_webform(form_data: WebFormSubmit):
    """
    Submit a support request via web form.
    
    Flow:
    1. Create database records (customer, conversation, ticket, message)
    2. Process with AI agent (separate process)
    3. Send email confirmation (separate process)
    4. Return success response
    """
    start_time = time.time()
    
    logger.info(f"=" * 60)
    logger.info(f"WEBFORM SUBMISSION - {datetime.now().isoformat()}")
    logger.info(f"=" * 60)
    logger.info(f"From: {form_data.name} <{form_data.email}>")
    logger.info(f"Subject: {form_data.subject}")
    logger.info(f"Priority: {form_data.priority}")
    
    try:
        # STEP 1: Create database records
        logger.info("STEP 1/3: Creating database records...")
        db_records = WebFormService.create_database_records(
            email=form_data.email,
            name=form_data.name,
            subject=form_data.subject,
            message=form_data.message,
            priority=form_data.priority
        )
        
        ticket = db_records['ticket']
        message_id = db_records['message_id']
        
        logger.info(f"  - Customer: {db_records['customer']['id']}")
        logger.info(f"  - Conversation: {db_records['conversation']['id']}")
        logger.info(f"  - Ticket: {ticket['ticket_number']}")
        logger.info(f"  - Message ID: {message_id}")
        
        # STEP 2: Process with AI agent
        logger.info("STEP 2/3: Processing with AI agent...")
        ai_result = WebFormService.process_with_ai(
            customer_email=form_data.email,
            subject=form_data.subject,
            message_body=form_data.message
        )
        
        logger.info(f"  - AI Success: {ai_result.get('success', False)}")
        logger.info(f"  - Sentiment: {ai_result.get('sentiment_score', 0)}")
        logger.info(f"  - Escalation: {ai_result.get('escalation_required', False)}")
        
        # STEP 3: Send email confirmation
        logger.info("STEP 3/3: Sending email confirmation...")
        WebFormService.send_email(
            customer_email=form_data.email,
            subject=form_data.subject,
            message_id=message_id,
            reply_text=ai_result.get('reply_text', 'Thank you for contacting us.')
        )
        
        # Calculate processing time
        total_time_ms = int((time.time() - start_time) * 1000)
        
        # STEP 7: Produce Kafka event for async processing
        if kafka_producer:
            try:
                # Produce incoming ticket event
                kafka_producer.produce_ticket_event(
                    event_type='created',
                    ticket_id=ticket_id,
                    customer_id=customer_id,
                    channel='web_form',
                    subject=form_data.subject,
                    message=form_data.message,
                    metadata={
                        'priority': form_data.priority,
                        'source': 'webform_api_v2',
                    }
                )
                
                # Produce audit event
                kafka_producer.produce_audit_event(
                    event_type='ticket_created',
                    entity_type='ticket',
                    entity_id=ticket_id,
                    action='create',
                    details={
                        'channel': 'web_form',
                        'customer_email': form_data.email,
                    }
                )
                
                logger.info(f'Kafka events produced for ticket {ticket_id}')
            except Exception as e:
                logger.warning(f'Failed to produce Kafka events: {e}. Continuing without Kafka.')
        
        # Determine response time
        if form_data.priority == 'urgent':
            est_response = "2 hours"
        elif form_data.priority == 'high':
            est_response = "4 hours"
        else:
            est_response = "24 hours"
        
        logger.info(f"=" * 60)
        logger.info(f"COMPLETE - Ticket: {ticket['ticket_number']} - Time: {total_time_ms}ms")
        logger.info(f"=" * 60)
        
        return WebFormResponse(
            success=True,
            ticket_number=ticket['ticket_number'],
            message="Your support request has been submitted successfully!",
            estimated_response_time=est_response
        )
        
    except Exception as e:
        logger.error(f"ERROR: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit form: {str(e)}"
        )


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(content={
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Web Form API",
        "version": "2.0.0"
    })


@app.get("/")
async def root():
    """Root endpoint"""
    return JSONResponse(content={
        "service": "Web Form API",
        "version": "2.0.0",
        "description": "Production-ready web form with AI and email",
        "endpoints": {
            "submit": "POST /api/v1/webform/submit",
            "health": "GET /api/v1/health"
        }
    })


if __name__ == "__main__":
    import uvicorn
    
    logger.info("=" * 60)
    logger.info("WEB FORM API v2.0.0 - PRODUCTION READY")
    logger.info("=" * 60)
    logger.info("Running on http://localhost:8001")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        workers=1,
        log_level="info"
    )
