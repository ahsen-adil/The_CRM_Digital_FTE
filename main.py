"""
Unified CRM System - Single Server

Runs all services from a single FastAPI application:
- API Server (Port 8002)
- Webform API (Port 8001) 
- WhatsApp Webhook (Port 8000)
- Email Polling (Background task)

All logs appear in unified output.
Single command to start everything.
"""
import asyncio
import logging
import sys
import os
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure unified logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('CRM_SYSTEM')


# =============================================================================
# Background Tasks
# =============================================================================

async def email_polling_task():
    """Background task for email polling"""
    from src.channels.email_handler import EmailHandler
    from production.database.repository import create_customer, create_conversation, create_ticket
    from production.agent.customer_success_agent import run_agent_sync
    
    logger.info("Email polling background task started")
    
    handler = EmailHandler()
    
    def process_email(email_data):
        """Process incoming email"""
        try:
            logger.info(f"📧 Processing email from {email_data['from']}: {email_data['subject']}")
            
            # Create customer
            customer = create_customer(email=email_data['from'])
            
            # Create conversation
            conversation = create_conversation(
                customer_id=customer['id'],
                topic=email_data['subject']
            )
            
            # Create ticket
            ticket = create_ticket(
                customer_id=customer['id'],
                channel='email',
                description=email_data['body'],
                subject=email_data['subject'],
                conversation_id=conversation['id']
            )
            
            # Generate AI response
            ai_response = run_agent_sync(
                customer_email=email_data['from'],
                subject=email_data['subject'],
                message_body=email_data['body']
            )
            
            # Send reply
            handler.send_reply(email_data, ai_response.reply_text)
            
            logger.info(f"✅ Email processed. Ticket: {ticket['ticket_number']}")
            
            return {
                'ticket_id': ticket['id'],
                'sentiment_score': ai_response.sentiment_score,
                'escalation_triggered': ai_response.escalation_required
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to process email: {e}")
            return None
    
    while True:
        try:
            handler.poll_emails(process_email)
            await asyncio.sleep(60)  # Poll every 60 seconds
        except Exception as e:
            logger.error(f"Email polling error: {e}")
            await asyncio.sleep(10)


async def kafka_worker_task():
    """Background task for Kafka workers"""
    try:
        from production.workers.kafka_workers import AgentProcessingWorker, EmailNotificationWorker, WhatsAppNotificationWorker, EscalationWorker
        
        logger.info("Kafka workers background task started")
        
        # Initialize workers
        workers = {
            'Agent': AgentProcessingWorker(),
            'Email': EmailNotificationWorker(),
            'WhatsApp': WhatsAppNotificationWorker(),
            'Escalation': EscalationWorker()
        }
        
        logger.info(f"Kafka workers initialized: {list(workers.keys())}")
        
        # Note: In production, you'd start the consumers here
        # For now, just keep the task alive
        while True:
            await asyncio.sleep(60)
            logger.debug("Kafka workers heartbeat")
            
    except Exception as e:
        logger.error(f"Kafka workers error: {e}")


# =============================================================================
# Lifespan Events
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown"""
    
    # STARTUP
    logger.info("="*80)
    logger.info("🚀 STARTING CRM SYSTEM - ALL SERVICES")
    logger.info("="*80)
    
    # Initialize Kafka
    try:
        from production.utils.kafka_producer import init_kafka_producer
        from production.config import settings
        kafka_producer = init_kafka_producer(settings.KAFKA_BOOTSTRAP_SERVERS)
        logger.info("✅ Kafka producer initialized")
    except Exception as e:
        logger.warning(f"⚠️  Kafka producer initialization skipped: {e}")
    
    # Start background tasks
    logger.info("Starting background tasks...")
    
    background_tasks = [
        asyncio.create_task(email_polling_task(), name="Email_Polling"),
        asyncio.create_task(kafka_worker_task(), name="Kafka_Workers")
    ]
    
    logger.info(f"✅ Background tasks started: {len(background_tasks)}")
    logger.info("="*80)
    
    yield
    
    # SHUTDOWN
    logger.info("="*80)
    logger.info("🛑 SHUTTING DOWN CRM SYSTEM")
    logger.info("="*80)
    
    # Cancel background tasks
    logger.info("Cancelling background tasks...")
    for task in background_tasks:
        task.cancel()
    
    await asyncio.gather(*background_tasks, return_exceptions=True)
    logger.info("✅ Background tasks cancelled")
    
    logger.info("="*80)
    logger.info("✅ CRM SYSTEM SHUTDOWN COMPLETE")
    logger.info("="*80)


# =============================================================================
# Create Main Application
# =============================================================================

app = FastAPI(
    title="Customer Success Digital FTE - Unified",
    description="Unified CRM system with Email, WhatsApp, and Webform support",
    version="3.0.0",
    lifespan=lifespan
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Include Routers from Existing Services
# =============================================================================

# Import routes from existing services
@app.get("/health")
async def health_check():
    """Unified health check"""
    return {
        "status": "healthy",
        "service": "CRM System - Unified",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Customer Success Digital FTE",
        "version": "3.0.0",
        "channels": ["email", "whatsapp", "webform"],
        "status": "running"
    }


# Include webform routes
try:
    from webform_api_v2 import app as webform_app
    app.router.routes.extend([
        route for route in webform_app.router.routes
        if route.path.startswith('/api/v1/webform')
    ])
    logger.info("✅ Webform API routes included")
except Exception as e:
    logger.warning(f"⚠️  Webform API routes not included: {e}")


# Include WhatsApp webhook routes
try:
    from whatsapp_webhook_kafka import app as whatsapp_app
    app.router.routes.extend([
        route for route in whatsapp_app.router.routes
        if route.path.startswith('/whatsapp')
    ])
    logger.info("✅ WhatsApp Webhook routes included")
except Exception as e:
    logger.warning(f"⚠️  WhatsApp Webhook routes not included: {e}")


# Include API server routes
try:
    from production.api.main import app as api_app
    app.router.routes.extend([
        route for route in api_app.router.routes
        if route.path.startswith('/api/v1')
    ])
    logger.info("✅ API Server routes included")
except Exception as e:
    logger.warning(f"⚠️  API Server routes not included: {e}")


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    logger.info("="*80)
    logger.info("🎯 UNIFIED CRM SYSTEM")
    logger.info("="*80)
    logger.info("Starting all services on port 8002...")
    logger.info("  - API Server: http://localhost:8002")
    logger.info("  - Webform API: http://localhost:8002/api/v1/webform")
    logger.info("  - WhatsApp Webhook: http://localhost:8002/whatsapp-webhook")
    logger.info("  - Email Polling: Background task (every 60s)")
    logger.info("  - Kafka Workers: Background task")
    logger.info("="*80)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info"
    )
