"""
Web Form API - MINIMAL VERSION (No asyncio conflicts)
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import time
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


@app.post("/api/v1/webform/submit", response_model=WebFormResponse)
def submit_webform(form_data: WebFormSubmit):
    """Submit web form - SYNCHRONOUS, NO ASYNCIO"""
    import traceback as tb
    try:
        print(f"Received form: {form_data}")
        conn = get_db_conn()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Create customer
            cur.execute("SELECT * FROM customers WHERE email = %s", (form_data.email,))
            customer = cur.fetchone()
            if not customer:
                print(f"Creating new customer: {form_data.email}")
                cur.execute("INSERT INTO customers (email, name, preferred_channel) VALUES (%s, %s, 'web_form') RETURNING *", (form_data.email, form_data.name))
                customer = cur.fetchone()
            print(f"Customer ID: {customer['id']}")
            
            # Create conversation
            cur.execute("INSERT INTO conversations (customer_id, topic, status) VALUES (%s, %s, 'open') RETURNING *", (customer['id'], form_data.subject))
            conversation = cur.fetchone()
            print(f"Conversation ID: {conversation['id']}")
            
            # Create ticket
            cur.execute("INSERT INTO tickets (customer_id, channel, subject, description, conversation_id, status, priority) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING *", (customer['id'], 'web_form', form_data.subject, form_data.message, conversation['id'], 'open', form_data.priority))
            ticket = cur.fetchone()
            print(f"Ticket ID: {ticket['id']}, Number: {ticket['ticket_number']}")
            
            # Create message
            message_id = f"webform-{ticket['id']}"
            cur.execute("INSERT INTO messages (message_id, conversation_id, ticket_id, channel, direction, content) VALUES (%s, %s, %s, %s, %s, %s) RETURNING *", (message_id, conversation['id'], ticket['id'], 'web_form', 'inbound', form_data.message))
            
            conn.commit()
            print("All DB operations successful")
        
        conn.close()
        
        return WebFormResponse(
            success=True,
            ticket_number=ticket['ticket_number'],
            message="Form submitted successfully!"
        )
    except Exception as e:
        print(f"ERROR: {e}")
        print(tb.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/health")
def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn
    print("Starting Web Form API (MINIMAL)...")
    uvicorn.run(app, host="0.0.0.0", port=8001, workers=1)
