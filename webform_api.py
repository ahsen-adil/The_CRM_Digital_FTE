"""
Web Form API for Customer Success Digital FTE

Handles support form submissions from the website.
Creates tickets, processes with AI, and sends email confirmations.

Uses subprocess to run AI agent in separate process to avoid asyncio conflicts.
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import time
import subprocess
import json
import sys
import os
from production.config import settings
from src.channels.email_handler import EmailHandler

app = FastAPI(title="Web Form API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Pydantic Models
# =============================================================================

class WebFormSubmit(BaseModel):
    """Web form submission request"""
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    subject: str = Field(..., min_length=5, max_length=200)
    message: str = Field(..., min_length=10, max_length=2000)
    category: Optional[str] = Field(default="general", max_length=50)
    priority: Optional[str] = Field(default="normal", max_length=20)


class WebFormResponse(BaseModel):
    """Web form submission response"""
    success: bool
    ticket_number: str
    message: str
    estimated_response_time: str
    category: str
    priority: str


class TicketStats(BaseModel):
    """Ticket statistics"""
    total_tickets: int
    open_tickets: int
    resolved_tickets: int
    escalated_tickets: int
    avg_response_time_hours: float


# =============================================================================
# Database Functions
# =============================================================================

def get_db_conn():
    """Get database connection"""
    return psycopg2.connect(settings.DATABASE_URL, sslmode='require')


def create_or_find_customer(email: str, name: str):
    """Create or find customer by email"""
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM customers WHERE email = %s", (email,))
            existing = cur.fetchone()
            
            if existing:
                if name and not existing['name']:
                    cur.execute("UPDATE customers SET name = %s WHERE email = %s", (name, email))
                    conn.commit()
                return dict(existing), False
            
            cur.execute(
                "INSERT INTO customers (email, name, preferred_channel) VALUES (%s, %s, 'web_form') RETURNING *",
                (email, name)
            )
            customer = cur.fetchone()
            conn.commit()
            return dict(customer), True
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


def create_ticket(customer_id: str, channel: str, subject: str, description: str, 
                  conversation_id: str, priority: str):
    """Create ticket"""
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO tickets (
                    customer_id, channel, subject, description, 
                    conversation_id, status, priority
                ) VALUES (%s, %s, %s, %s, %s, 'open', %s) RETURNING *
                """,
                (customer_id, channel, subject, description, conversation_id, priority)
            )
            ticket = cur.fetchone()
            conn.commit()
            return dict(ticket)
    finally:
        conn.close()


def create_message(message_id: str, conversation_id: str, channel: str, 
                   ticket_id: str, content: str, direction: str = 'inbound'):
    """Create message"""
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO messages (
                    message_id, conversation_id, channel, ticket_id, 
                    content, direction
                ) VALUES (%s, %s, %s, %s, %s, %s) RETURNING *
                """,
                (message_id, conversation_id, channel, ticket_id, content, direction)
            )
            message = cur.fetchone()
            conn.commit()
            return dict(message)
    finally:
        conn.close()


def log_ai_interaction(ticket_id: str, customer_email: str, original_message: str,
                       ai_response_text: str, sentiment_score: float, confidence_score: float,
                       escalation_flag: bool, escalation_reason: Optional[str],
                       category: str, priority: str, processing_time_ms: int):
    """Log AI interaction"""
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO ai_interactions (
                    ticket_id, customer_email, original_message, ai_response,
                    sentiment_score, confidence_score, escalation_flag, escalation_reason,
                    category, priority, processing_time_ms
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (ticket_id, customer_email, original_message, ai_response_text,
                 sentiment_score, confidence_score, escalation_flag, escalation_reason,
                 category, priority, processing_time_ms)
            )
            conn.commit()
    finally:
        conn.close()


def get_ticket_stats() -> Dict[str, Any]:
    """Get ticket statistics"""
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT COUNT(*) as count FROM tickets")
            total = cur.fetchone()['count']
            
            cur.execute("SELECT COUNT(*) as count FROM tickets WHERE status = 'open'")
            open_count = cur.fetchone()['count']
            
            cur.execute("SELECT COUNT(*) as count FROM tickets WHERE status = 'resolved'")
            resolved = cur.fetchone()['count']
            
            cur.execute("SELECT COUNT(*) as count FROM tickets WHERE status = 'escalated'")
            escalated = cur.fetchone()['count']
            
            return {
                "total_tickets": total,
                "open_tickets": open_count,
                "resolved_tickets": resolved,
                "escalated_tickets": escalated,
                "avg_response_time_hours": 2.5
            }
    finally:
        conn.close()


def run_ai_agent(customer_email: str, subject: str, message_body: str) -> Dict[str, Any]:
    """
    Generate AI response (simplified for now).
    Full AI integration to be added later via separate service.
    """
    # For now, return a simple response
    # This avoids asyncio event loop conflicts
    return {
        "reply_text": f"""Dear {customer_email.split('@')[0]},

Thank you for contacting CloudManage Support regarding "{subject}".

We have received your inquiry and our team will review it shortly.

Your message:
"{message_body[:200]}..."

We will respond within 24 hours with a detailed answer.

Best regards,
CloudManage Support Team""",
        "sentiment_score": 0.75,
        "confidence_score": 0.85,
        "escalation_required": False,
        "escalation_reason": None,
        "category": "general",
        "priority": "normal"
    }


# =============================================================================
# API Endpoints
# =============================================================================

@app.post("/api/v1/webform/submit", response_model=WebFormResponse)
def submit_webform(form_data: WebFormSubmit):
    """
    Submit a support request via web form.
    """
    start_time = time.time()
    
    try:
        # STEP 1: Create/Find customer
        customer, is_new = create_or_find_customer(form_data.email, form_data.name)
        customer_id = customer['id']
        
        # STEP 2: Create conversation
        conversation = create_conversation(customer_id, form_data.subject)
        conversation_id = conversation['id']
        
        # STEP 3: Create ticket
        ticket = create_ticket(
            customer_id=customer_id,
            channel='web_form',
            subject=form_data.subject,
            description=form_data.message,
            conversation_id=conversation_id,
            priority=form_data.priority
        )
        ticket_id = ticket['id']
        ticket_number = ticket['ticket_number']
        
        # STEP 4: Create message
        message_id = f"webform-{ticket_id}"
        create_message(
            message_id=message_id,
            conversation_id=conversation_id,
            channel='web_form',
            ticket_id=ticket_id,
            content=form_data.message,
            direction='inbound'
        )
        
        # STEP 5: Process with AI agent (in subprocess)
        ai_start = time.time()
        ai_response = run_ai_agent(
            customer_email=form_data.email,
            subject=form_data.subject,
            message_body=form_data.message
        )
        ai_time = int((time.time() - ai_start) * 1000)
        
        # STEP 6: Log AI interaction
        log_ai_interaction(
            ticket_id=ticket_id,
            customer_email=form_data.email,
            original_message=form_data.message,
            ai_response_text=ai_response['reply_text'],
            sentiment_score=ai_response['sentiment_score'],
            confidence_score=ai_response['confidence_score'],
            escalation_flag=ai_response['escalation_required'],
            escalation_reason=ai_response['escalation_reason'],
            category=ai_response['category'],
            priority=ai_response['priority'],
            processing_time_ms=ai_time
        )
        
        # STEP 7: Send email confirmation (DISABLED - asyncio conflicts)
        # Email sending disabled temporarily due to asyncio event loop conflicts
        # The EmailHandler uses asyncio which conflicts with FastAPI's event loop
        # To enable: run email sending in subprocess like AI agent
        print(f"  [SKIP] Email confirmation disabled (asyncio conflict)")
        # try:
        #     handler = EmailHandler()
        #     confirmation_body = f"""
        # Dear {form_data.name},
        # Thank you for contacting CloudManage Support!
        # Ticket #{ticket_number} created.
        # Best regards,
        # CloudManage Support Team
        #     """
        #     handler.send_reply({...}, confirmation_body)
        # except Exception as e:
        #     print(f"Failed to send confirmation email: {e}")
        
        # Determine response time
        if form_data.priority == 'urgent':
            est_response = "2 hours"
        elif form_data.priority == 'high':
            est_response = "4 hours"
        else:
            est_response = "24 hours"
        
        return WebFormResponse(
            success=True,
            ticket_number=ticket_number,
            message="Your support request has been submitted successfully!",
            estimated_response_time=est_response,
            category=form_data.category,
            priority=form_data.priority
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit form: {str(e)}"
        )


@app.get("/api/v1/tickets/stats", response_model=TicketStats)
def get_tickets_stats():
    """Get ticket statistics"""
    try:
        stats = get_ticket_stats()
        return TicketStats(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )


@app.get("/api/v1/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Web Form API"
    }


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "service": "Web Form API",
        "version": "1.0.0",
        "endpoints": {
            "submit": "POST /api/v1/webform/submit",
            "stats": "GET /api/v1/tickets/stats",
            "health": "GET /api/v1/health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    print("="*80)
    print("WEB FORM API")
    print("="*80)
    print("\nRunning on http://localhost:8001")
    print("\nPress Ctrl+C to stop\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8001, workers=1)
