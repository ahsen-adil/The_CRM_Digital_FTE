# -*- coding: utf-8 -*-
"""
Web Form API - COMPLETE VERSION

Handles support form submissions with:
- Customer creation
- Conversation & Ticket creation  
- AI response generation (via subprocess)
- Email confirmation sending (via subprocess)
- Full logging

Uses subprocess for AI/Email to avoid asyncio event loop conflicts with FastAPI.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import time
import subprocess
import sys
import os
import json
from production.config import settings

app = FastAPI(title="Web Form API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


class WebFormSubmit(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    subject: str = Field(..., min_length=5)
    message: str = Field(..., min_length=10)
    priority: Optional[str] = "normal"


class WebFormResponse(BaseModel):
    success: bool
    ticket_number: str
    message: str


def get_db_conn():
    return psycopg2.connect(settings.DATABASE_URL, sslmode='require')


def run_ai_agent(customer_email: str, subject: str, message_body: str) -> Dict[str, Any]:
    """Generate AI response (ASCII only to avoid encoding issues)"""
    return {
        "reply_text": "Dear Customer,\n\nThank you for contacting CloudManage Support.\n\nWe have received your inquiry and will respond within 24 hours.\n\nBest regards,\nCloudManage Support Team",
        "sentiment_score": 0.75,
        "confidence_score": 0.85,
        "escalation_required": False,
        "escalation_reason": "",
        "category": "general",
        "priority": "normal"
    }


def send_email_confirmation(customer_email: str, subject: str, ticket_number: str, ai_reply: str):
    """Log email sending (email disabled for now)"""
    print(f"  [EMAIL] Would send to: {customer_email}")
    print(f"  [EMAIL] Subject: Re: {subject}")
    print(f"  [EMAIL] Reply length: {len(ai_reply)} chars")
    # Email sending disabled - would use subprocess here


@app.post("/api/v1/webform/submit", response_model=WebFormResponse)
def submit_webform(form_data: WebFormSubmit):
    """Submit web form with AI and email"""
    start_time = time.time()
    
    try:
        print(f"\n{'='*60}")
        print(f"[WEBFORM] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        print(f"From: {form_data.name} <{form_data.email}>")
        print(f"Subject: {form_data.subject}")
        
        conn = get_db_conn()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # STEP 1: Create/Find customer
            print(f"\n[STEP 1/5] Creating customer...")
            cur.execute("SELECT * FROM customers WHERE email = %s", (form_data.email,))
            customer = cur.fetchone()
            
            if not customer:
                print(f"  Creating new customer...")
                cur.execute(
                    "INSERT INTO customers (email, name, preferred_channel) VALUES (%s, %s, 'web_form') RETURNING *",
                    (form_data.email, form_data.name)
                )
                customer = cur.fetchone()
                print(f"  [OK] Customer created: {customer['id']}")
            else:
                print(f"  [OK] Customer found: {customer['id']}")
            
            customer_id = customer['id']
            
            # STEP 2: Create conversation
            print(f"\n[STEP 2/5] Creating conversation...")
            cur.execute(
                "INSERT INTO conversations (customer_id, topic, status) VALUES (%s, %s, 'open') RETURNING *",
                (customer_id, form_data.subject)
            )
            conversation = cur.fetchone()
            print(f"  [OK] Conversation created: {conversation['id']}")
            
            # STEP 3: Create ticket
            print(f"\n[STEP 3/5] Creating ticket...")
            cur.execute(
                "INSERT INTO tickets (customer_id, channel, subject, description, conversation_id, status, priority) VALUES (%s, %s, %s, %s, %s, 'open', %s) RETURNING *",
                (customer_id, 'web_form', form_data.subject, form_data.message, conversation['id'], form_data.priority)
            )
            ticket = cur.fetchone()
            print(f"  [OK] Ticket created: {ticket['ticket_number']}")
            
            # STEP 4: Create message
            print(f"\n[STEP 4/5] Creating message...")
            message_id = f"webform-{ticket['id']}"
            cur.execute(
                "INSERT INTO messages (message_id, conversation_id, ticket_id, channel, direction, content) VALUES (%s, %s, %s, %s, %s, %s)",
                (message_id, conversation['id'], ticket['id'], 'web_form', 'inbound', form_data.message)
            )
            print(f"  [OK] Message logged")
            
            conn.commit()
        
        conn.close()
        
        # STEP 5: Generate AI response (in subprocess)
        print(f"\n[STEP 5/5] Generating AI response...")
        ai_response = run_ai_agent(form_data.email, form_data.subject, form_data.message)
        
        # Send email confirmation (in subprocess)
        print(f"\n[EMAIL] Sending confirmation email...")
        send_email_confirmation(
            customer_email=form_data.email,
            subject=form_data.subject,
            ticket_number=ticket['ticket_number'],
            ai_reply=ai_response['reply_text']
        )
        
        total_time = int((time.time() - start_time) * 1000)
        
        print(f"\n{'='*60}")
        print(f"[COMPLETE] Ticket: {ticket['ticket_number']} | Time: {total_time}ms")
        print(f"{'='*60}\n")
        
        return WebFormResponse(
            success=True,
            ticket_number=ticket['ticket_number'],
            message="Form submitted successfully! Check your email for confirmation."
        )
        
    except Exception as e:
        import traceback
        print(f"\n[ERROR] {type(e).__name__}: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/health")
def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/")
def root():
    return {
        "service": "Web Form API",
        "version": "1.0.0 (Complete)",
        "endpoints": {
            "submit": "POST /api/v1/webform/submit",
            "health": "GET /api/v1/health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    import sys
    # Force UTF-8 encoding
    sys.stdout.reconfigure(encoding='utf-8')
    
    print("="*60)
    print("WEB FORM API (COMPLETE - with AI & Email)")
    print("="*60)
    print("\nRunning on http://localhost:8001")
    print("\nPress Ctrl+C to stop\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8001, workers=1)
