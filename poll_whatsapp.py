"""
100% SYNCHRONOUS WhatsApp Polling Service

Polls for new WhatsApp messages and auto-replies with AI-generated responses.
Uses the same robust pattern as email polling.

Usage: python poll_whatsapp.py

Or with custom interval:
    python poll_whatsapp.py --interval 20
"""
import sys
import os
import time
import signal
import argparse
import traceback
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from src.channels.whatsapp_handler import WhatsAppHandler, get_whatsapp_metrics
from production.config import settings
from production.agent.customer_success_agent import run_agent_sync

running = True

def signal_handler(sig, frame):
    global running
    print("\n\n[SHUTDOWN] Stopping...")
    running = False


def get_db_conn():
    """Get synchronous database connection"""
    return psycopg2.connect(settings.DATABASE_URL, sslmode='require')


def create_customer_whatsapp(phone_number, name=None):
    """Create/find customer by WhatsApp number"""
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if exists
            cur.execute("SELECT * FROM customers WHERE phone_number = %s", (phone_number,))
            existing = cur.fetchone()
            
            if existing:
                print(f"  [OK] Found customer: {existing['id']}")
                return dict(existing)
            
            # Create new
            cur.execute(
                "INSERT INTO customers (phone_number, name) VALUES (%s, %s) RETURNING *",
                (phone_number, name)
            )
            customer = cur.fetchone()
            conn.commit()
            print(f"  [OK] Created customer: {customer['id']}")
            return dict(customer)
    finally:
        conn.close()


def create_conversation(customer_id, topic):
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
            print(f"  [OK] Created conversation: {conversation['id']}")
            return dict(conversation)
    finally:
        conn.close()


def create_ticket(customer_id, channel, description, conversation_id):
    """Create ticket"""
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO tickets (customer_id, channel, description, conversation_id, status)
                VALUES (%s, %s, %s, %s, 'open') RETURNING *
                """,
                (customer_id, channel, description, conversation_id)
            )
            ticket = cur.fetchone()
            conn.commit()
            print(f"  [OK] Created ticket: {ticket['id']} | {ticket['ticket_number']}")
            return dict(ticket)
    finally:
        conn.close()


def log_ai_interaction(ticket_id, customer_email, original_message, ai_response,
                       sentiment_score, confidence_score, escalation_flag,
                       escalation_reason, category, priority, processing_time_ms):
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
                (ticket_id, customer_email, original_message, ai_response,
                 sentiment_score, confidence_score, escalation_flag, escalation_reason,
                 category, priority, processing_time_ms)
            )
            conn.commit()
            print(f"  [OK] Logged AI interaction")
    finally:
        conn.close()


def process_whatsapp_message(message_data):
    """Process WhatsApp message with AI"""
    print(f"\n{'='*80}")
    print(f"[WHATSAPP MESSAGE] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    print(f"From: {message_data.get('from_name', 'Unknown')} ({message_data.get('from', '')})")
    print(f"Message: {message_data.get('body', '')[:100]}")
    print(f"{'='*80}\n")
    
    start = time.time()
    result = {'success': False, 'error': None, 'ticket_id': None}
    
    try:
        phone_number = message_data.get('from', '').split('@')[0]  # Remove @c.us
        customer_name = message_data.get('from_name', 'WhatsApp User')
        message_body = message_data.get('body', '')
        
        # STEP 1: Customer
        print("[STEP 1/7] Creating customer...")
        customer = create_customer_whatsapp(phone_number, customer_name)
        customer_id = customer['id']
        
        # STEP 2: Conversation
        print("[STEP 2/7] Creating conversation...")
        conversation = create_conversation(customer_id, "WhatsApp Support")
        conversation_id = conversation['id']
        
        # STEP 3: Ticket
        print("[STEP 3/7] Creating ticket...")
        ticket = create_ticket(
            customer_id=customer_id,
            channel='whatsapp',
            description=message_body,
            conversation_id=conversation_id
        )
        ticket_id = ticket['id']
        ticket_number = ticket['ticket_number']
        result['ticket_id'] = ticket_id
        
        # STEP 4: AI Agent
        print("[STEP 4/7] Calling AI agent...")
        ai_start = time.time()
        ai_response = run_agent_sync(
            customer_email=f"{phone_number}@whatsapp.com",  # Use phone as email
            subject="WhatsApp Support",
            message_body=message_body
        )
        ai_time = int((time.time() - ai_start) * 1000)
        print(f"  [OK] AI: {ai_time}ms | Sentiment: {ai_response.sentiment_score} | Escalation: {ai_response.escalation_required}")
        
        # STEP 5: Log AI
        print("[STEP 5/7] Logging AI interaction...")
        log_ai_interaction(
            ticket_id=ticket_id,
            customer_email=f"{phone_number}@whatsapp.com",
            original_message=message_body,
            ai_response=ai_response.reply_text,
            sentiment_score=ai_response.sentiment_score,
            confidence_score=ai_response.confidence_score,
            escalation_flag=ai_response.escalation_required,
            escalation_reason=ai_response.escalation_reason,
            category=ai_response.category,
            priority=ai_response.priority,
            processing_time_ms=ai_time
        )
        
        # STEP 6: Escalation
        print("[STEP 6/7] Checking escalation...")
        if ai_response.escalation_required:
            print(f"  [WARN] Escalation: {ai_response.escalation_reason}")
        else:
            print(f"  [OK] No escalation")
        
        # STEP 7: WhatsApp Reply
        print("[STEP 7/7] Sending WhatsApp reply...")
        handler = WhatsAppHandler()
        
        # Format response for WhatsApp (shorter, more conversational)
        whatsapp_response = format_for_whatsapp(ai_response.reply_text)
        
        success = handler.send_reply(message_data, whatsapp_response)
        print(f"  [OK] Reply sent: {success}")
        
        total_time = int((time.time() - start) * 1000)
        result['success'] = True
        
        print(f"\n{'='*80}")
        print(f"[COMPLETE] Ticket: {ticket_number} | Time: {total_time}ms")
        print(f"{'='*80}\n")
        
        return result
        
    except Exception as e:
        print(f"\n{'='*80}")
        print(f"[ERROR] {type(e).__name__}: {e}")
        print(f"{'='*80}")
        traceback.print_exc()
        result['error'] = str(e)
        return result


def format_for_whatsapp(text):
    """Format response for WhatsApp (shorter, conversational)"""
    # Truncate to ~500 chars for WhatsApp
    if len(text) > 500:
        text = text[:500] + "..."
    return text


# Simulated webhook messages (for testing without actual webhook)
# In production, replace with actual webhook endpoint
webhook_messages_queue = []

def poll_webhook_messages():
    """
    Poll for new WhatsApp messages.
    
    For production: implement actual webhook endpoint with FastAPI/Flask
    For testing: use simulated messages
    """
    # In production, this would call actual webhook endpoint
    # For now, return empty list
    return []


def main():
    global running
    
    print("="*80)
    print("WHATSAPP POLLING SERVICE")
    print("Auto-reply to WhatsApp messages with AI")
    print("="*80)
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--interval', '-i', type=int, default=30)
    args = parser.parse_args()
    
    print(f"Interval: {args.interval}s\n")
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Test database
    print("[TEST] Database connection...")
    try:
        conn = get_db_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            result = cur.fetchone()
            print(f"[OK] Database connected (test: {result[0]})\n")
        conn.close()
    except Exception as e:
        print(f"[ERROR] Database failed: {e}\n")
        traceback.print_exc()
        sys.exit(1)
    
    # Test WhatsApp API
    print("[TEST] WhatsApp API connection...")
    try:
        handler = WhatsAppHandler()
        if handler.check_connection():
            print("[OK] WhatsApp API connected\n")
        else:
            print("[WARN] WhatsApp API not configured - check WHAPI_API_KEY in .env\n")
    except Exception as e:
        print(f"[ERROR] WhatsApp API failed: {e}\n")
        traceback.print_exc()
        # Continue anyway for testing
    
    print("="*80)
    print("WHATSAPP POLLING READY")
    print("="*80)
    print("\nNote: For production, set up webhook endpoint at:")
    print("  https://your-server.com/whatsapp-webhook")
    print("\nConfigure webhook in Whapi dashboard:")
    print("  Settings → Webhooks → Add webhook URL")
    print("\nPress Ctrl+C to stop\n")
    
    handler = WhatsAppHandler()
    poll_count = 0
    
    while running:
        poll_count += 1
        ts = datetime.now().strftime('%H:%M:%S')
        
        try:
            print(f"[{ts}] Poll #{poll_count}...")
            
            # Poll for new messages
            messages = poll_webhook_messages()
            
            if messages:
                print(f"[{ts}] Found {len(messages)} message(s)")
                
                for msg in messages:
                    process_whatsapp_message(msg)
            else:
                print(f"[{ts}] No new messages")
                
        except Exception as e:
            print(f"[{ts}] [ERROR] {type(e).__name__}: {e}")
            traceback.print_exc()
        
        if running:
            time.sleep(args.interval)
    
    print("\n[SHUTDOWN] Stopped")


if __name__ == '__main__':
    main()
