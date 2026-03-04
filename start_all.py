"""
Unified CRM System Startup

Runs all services from a single command:
- API Server (Port 8002)
- Webform API (Port 8001)
- WhatsApp Webhook (Port 8000)
- Email Polling (Background task)
- Kafka Workers (Optional)

All logs appear in unified output.
"""
import asyncio
import logging
import sys
import os
import signal
from datetime import datetime
from typing import List, Callable
import threading
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure unified logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('CRM_SYSTEM')


class ServiceManager:
    """Manages all CRM services"""
    
    def __init__(self):
        self.running = True
        self.services = {}
        self.threads = []
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.running = False
    
    def register_service(self, name: str, startup_func: Callable, shutdown_func: Callable = None):
        """Register a service"""
        self.services[name] = {
            'startup': startup_func,
            'shutdown': shutdown_func,
            'running': False
        }
        logger.info(f"Service registered: {name}")
    
    def start_service_thread(self, name: str):
        """Start a service in a separate thread"""
        def run_service():
            service = self.services[name]
            try:
                logger.info(f"Starting service: {name}")
                service['startup']()
                service['running'] = True
                logger.info(f"Service started: {name}")
            except Exception as e:
                logger.error(f"Service {name} failed to start: {e}")
                service['running'] = False
        
        thread = threading.Thread(target=run_service, name=name, daemon=True)
        thread.start()
        self.threads.append(thread)
        logger.info(f"Service thread started: {name}")
    
    def start_all(self):
        """Start all registered services"""
        logger.info("="*80)
        logger.info("STARTING CRM SYSTEM - ALL SERVICES")
        logger.info("="*80)
        
        for name in self.services:
            self.start_service_thread(name)
        
        logger.info("="*80)
        logger.info("ALL SERVICES STARTED")
        logger.info("="*80)
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
                
                # Check service health
                for name, service in self.services.items():
                    if service['running']:
                        logger.debug(f"Service {name}: RUNNING")
                    else:
                        logger.warning(f"Service {name}: NOT RUNNING")
                        
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            self.shutdown_all()
    
    def shutdown_all(self):
        """Shutdown all services gracefully"""
        logger.info("="*80)
        logger.info("SHUTTING DOWN CRM SYSTEM")
        logger.info("="*80)
        
        self.running = False
        
        # Shutdown services
        for name, service in self.services.items():
            try:
                logger.info(f"Shutting down service: {name}")
                if service['shutdown']:
                    service['shutdown']()
                service['running'] = False
                logger.info(f"Service shutdown complete: {name}")
            except Exception as e:
                logger.error(f"Error shutting down {name}: {e}")
        
        # Wait for threads
        logger.info("Waiting for service threads to complete...")
        for thread in self.threads:
            thread.join(timeout=5)
        
        logger.info("="*80)
        logger.info("CRM SYSTEM SHUTDOWN COMPLETE")
        logger.info("="*80)


# =============================================================================
# Service Startup Functions
# =============================================================================

def start_api_server():
    """Start API Server (Port 8002)"""
    import uvicorn
    from production.api.main import app  # You'll need to create this
    
    logger.info("Starting API Server on port 8002...")
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")


def start_webform_api():
    """Start Webform API (Port 8001)"""
    import uvicorn
    from webform_api_v2 import app
    
    logger.info("Starting Webform API on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")


def start_whatsapp_webhook():
    """Start WhatsApp Webhook (Port 8000)"""
    import uvicorn
    from whatsapp_webhook_kafka import app
    
    logger.info("Starting WhatsApp Webhook on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


def start_email_polling():
    """Start Email Polling Service"""
    from src.channels.email_handler import EmailHandler
    from production.database.repository import create_customer, create_conversation, create_ticket
    from production.agent.customer_success_agent import run_agent_sync
    import time
    
    logger.info("Starting Email Polling Service...")
    
    handler = EmailHandler()
    
    def process_email(email_data):
        """Process incoming email"""
        try:
            logger.info(f"Processing email from {email_data['from']}: {email_data['subject']}")
            
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
            
            logger.info(f"Email processed successfully. Ticket: {ticket['ticket_number']}")
            
            return {
                'ticket_id': ticket['id'],
                'sentiment_score': ai_response.sentiment_score,
                'escalation_triggered': ai_response.escalation_required
            }
            
        except Exception as e:
            logger.error(f"Failed to process email: {e}")
            return None
    
    # Poll emails
    while True:
        try:
            handler.poll_emails(process_email)
            time.sleep(60)  # Poll every 60 seconds
        except Exception as e:
            logger.error(f"Email polling error: {e}")
            time.sleep(10)


def start_kafka_workers():
    """Start Kafka Workers"""
    from production.workers.kafka_workers import run_all_workers
    
    logger.info("Starting Kafka Workers...")
    run_all_workers()


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """Main entry point - starts all services"""
    from production.config import settings
    
    # Initialize Kafka producer (shared)
    try:
        from production.utils.kafka_producer import init_kafka_producer
        kafka_producer = init_kafka_producer(settings.KAFKA_BOOTSTRAP_SERVERS)
        logger.info("Kafka producer initialized")
    except Exception as e:
        logger.warning(f"Kafka producer initialization skipped: {e}")
    
    # Create service manager
    manager = ServiceManager()
    
    # Register services
    manager.register_service("API_Server", lambda: start_api_server())
    manager.register_service("Webform_API", lambda: start_webform_api())
    manager.register_service("WhatsApp_Webhook", lambda: start_whatsapp_webhook())
    manager.register_service("Email_Polling", lambda: start_email_polling())
    # manager.register_service("Kafka_Workers", lambda: start_kafka_workers())  # Optional
    
    # Start all services
    manager.start_all()


if __name__ == "__main__":
    main()
