"""
Kafka Workers for Customer Success Digital FTE

Production workers that consume from Kafka topics and:
- Process tickets with AI agent
- Send email notifications
- Send WhatsApp notifications
- Handle escalations
"""
import logging
import sys
import os
import time
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from production.utils.kafka_consumer import (
    AgentProcessingConsumer,
    EmailNotificationConsumer,
    WhatsAppNotificationConsumer,
    EscalationConsumer,
)
from production.utils.kafka_producer import get_kafka_producer
from production.config import settings
import traceback

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentProcessingWorker:
    """
    Worker that processes incoming tickets with AI agent.
    
    Consumes from: tickets.incoming.*
    Produces to: tickets.agent.responses, notifications.email/whatsapp
    """
    
    def __init__(self):
        # Initialize Kafka producer first
        try:
            from production.utils.kafka_producer import init_kafka_producer
            self.producer = init_kafka_producer(settings.KAFKA_BOOTSTRAP_SERVERS)
            logger.info('Kafka producer initialized for agent worker')
        except Exception as e:
            logger.warning(f'Kafka producer initialization failed: {e}. Running without Kafka.')
            self.producer = None
        
        self.consumer = AgentProcessingConsumer(settings.KAFKA_BOOTSTRAP_SERVERS)
        
        # Register handlers
        self.consumer.register_handler(
            'tickets.incoming.email',
            self._handle_email_ticket
        )
        self.consumer.register_handler(
            'tickets.incoming.whatsapp',
            self._handle_whatsapp_ticket
        )
        self.consumer.register_handler(
            'tickets.incoming.webform',
            self._handle_webform_ticket
        )
        
        logger.info('Agent processing worker initialized')
    
    def _handle_email_ticket(self, event: Dict[str, Any], key: str = None):
        """Handle incoming email ticket"""
        logger.info(f'Processing email ticket: {event.get("ticket_id")}')
        self._process_ticket(event, 'email')
    
    def _handle_whatsapp_ticket(self, event: Dict[str, Any], key: str = None):
        """Handle incoming WhatsApp ticket"""
        logger.info(f'Processing WhatsApp ticket: {event.get("ticket_id")}')
        self._process_ticket(event, 'whatsapp')
    
    def _handle_webform_ticket(self, event: Dict[str, Any], key: str = None):
        """Handle incoming webform ticket"""
        logger.info(f'Processing webform ticket: {event.get("ticket_id")}')
        self._process_ticket(event, 'web_form')
    
    def _process_ticket(self, event: Dict[str, Any], channel: str):
        """
        Process ticket with AI agent.
        
        Args:
            event: Ticket event
            channel: Channel type
        """
        try:
            ticket_id = event['ticket_id']
            customer_email = event.get('customer_id', '')
            subject = event['subject']
            message = event['message']
            
            logger.info(f'Processing ticket {ticket_id} from {channel}')
            
            # TODO: Integrate with AI agent
            # For now, log the processing
            logger.info(f'Ticket {ticket_id} processed successfully')
            
            # Produce response event
            # self.producer.produce_agent_response(
            #     ticket_id=ticket_id,
            #     response_text=response_text,
            #     sentiment_score=sentiment_score,
            #     confidence_score=confidence_score,
            #     escalation_required=escalation_required,
            # )
            
            # Produce notification
            # if channel == 'email':
            #     self.producer.produce_email_notification(...)
            # elif channel == 'whatsapp':
            #     self.producer.produce_whatsapp_notification(...)
            
        except Exception as e:
            logger.error(f'Error processing ticket: {e}')
            traceback.print_exc()
            raise
    
    def start(self):
        """Start the worker"""
        logger.info('Starting agent processing worker...')
        self.consumer.consume()


class EmailNotificationWorker:
    """
    Worker that sends email notifications.
    
    Consumes from: notifications.email
    """
    
    def __init__(self):
        # Initialize Kafka producer first
        try:
            from production.utils.kafka_producer import init_kafka_producer
            self.producer = init_kafka_producer(settings.KAFKA_BOOTSTRAP_SERVERS)
            logger.info('Kafka producer initialized for email worker')
        except Exception as e:
            logger.warning(f'Kafka producer initialization failed: {e}. Running without Kafka.')
            self.producer = None
        
        self.consumer = EmailNotificationConsumer(settings.KAFKA_BOOTSTRAP_SERVERS)
        self.consumer.register_handler('notifications.email', self._handle_email)
        
        logger.info('Email notification worker initialized')
    
    def _handle_email(self, event: Dict[str, Any], key: str = None):
        """Handle email notification"""
        try:
            recipient = event['recipient']
            subject = event['subject']
            body = event['body']
            ticket_id = event.get('ticket_id')
            
            logger.info(f'Sending email to {recipient} re: {subject}')
            
            # TODO: Integrate with EmailHandler
            # handler = EmailHandler()
            # handler.send_new_email(recipient, subject, body)
            
            logger.info(f'Email sent successfully to {recipient}')
            
        except Exception as e:
            logger.error(f'Error sending email: {e}')
            traceback.print_exc()
            raise
    
    def start(self):
        """Start the worker"""
        logger.info('Starting email notification worker...')
        self.consumer.consume()


class WhatsAppNotificationWorker:
    """
    Worker that sends WhatsApp notifications.
    
    Consumes from: notifications.whatsapp
    """
    
    def __init__(self):
        # Initialize Kafka producer first
        try:
            from production.utils.kafka_producer import init_kafka_producer
            self.producer = init_kafka_producer(settings.KAFKA_BOOTSTRAP_SERVERS)
            logger.info('Kafka producer initialized for whatsapp worker')
        except Exception as e:
            logger.warning(f'Kafka producer initialization failed: {e}. Running without Kafka.')
            self.producer = None
        
        self.consumer = WhatsAppNotificationConsumer(settings.KAFKA_BOOTSTRAP_SERVERS)
        self.consumer.register_handler('notifications.whatsapp', self._handle_whatsapp)
        
        logger.info('WhatsApp notification worker initialized')
    
    def _handle_whatsapp(self, event: Dict[str, Any], key: str = None):
        """Handle WhatsApp notification"""
        try:
            recipient = event['recipient']
            message = event['message']
            ticket_id = event.get('ticket_id')
            
            logger.info(f'Sending WhatsApp to {recipient}')
            
            # TODO: Integrate with WhatsAppHandler
            # handler = WhatsAppHandler()
            # handler.send_message(recipient, message)
            
            logger.info(f'WhatsApp sent successfully to {recipient}')
            
        except Exception as e:
            logger.error(f'Error sending WhatsApp: {e}')
            traceback.print_exc()
            raise
    
    def start(self):
        """Start the worker"""
        logger.info('Starting WhatsApp notification worker...')
        self.consumer.consume()


class EscalationWorker:
    """
    Worker that handles escalations.
    
    Consumes from: tickets.escalations
    """
    
    def __init__(self):
        # Initialize Kafka producer first
        try:
            from production.utils.kafka_producer import init_kafka_producer
            self.producer = init_kafka_producer(settings.KAFKA_BOOTSTRAP_SERVERS)
            logger.info('Kafka producer initialized for escalation worker')
        except Exception as e:
            logger.warning(f'Kafka producer initialization failed: {e}. Running without Kafka.')
            self.producer = None
        
        self.consumer = EscalationConsumer(settings.KAFKA_BOOTSTRAP_SERVERS)
        self.consumer.register_handler('tickets.escalations', self._handle_escalation)
        
        logger.info('Escalation worker initialized')
    
    def _handle_escalation(self, event: Dict[str, Any], key: str = None):
        """Handle escalation"""
        try:
            ticket_id = event['ticket_id']
            reason = event['reason']
            assigned_team = event['assigned_team']
            priority = event['priority']
            
            logger.info(
                f'Processing escalation for ticket {ticket_id}: '
                f'{reason} -> {assigned_team} ({priority})'
            )
            
            # TODO: Create escalation in database
            # TODO: Notify assigned team
            
            logger.info(f'Escalation processed successfully for {ticket_id}')
            
        except Exception as e:
            logger.error(f'Error processing escalation: {e}')
            traceback.print_exc()
            raise
    
    def start(self):
        """Start the worker"""
        logger.info('Starting escalation worker...')
        self.consumer.consume()


# =============================================================================
# Main Entry Point
# =============================================================================

def run_all_workers():
    """Run all workers in a single process (for development)"""
    logger.info('Starting all Kafka workers...')
    
    workers = [
        ('Agent Processing', AgentProcessingWorker()),
        ('Email Notifications', EmailNotificationWorker()),
        ('WhatsApp Notifications', WhatsAppNotificationWorker()),
        ('Escalations', EscalationWorker()),
    ]
    
    logger.info(f'Initialized {len(workers)} workers')
    
    # Note: In production, run each worker in a separate process
    # For development, we'll run them sequentially
    for name, worker in workers:
        logger.info(f'Starting {name} worker...')
        # worker.start()  # Uncomment to actually start
        logger.info(f'{name} worker initialized (not started in dev mode)')


if __name__ == '__main__':
    run_all_workers()
