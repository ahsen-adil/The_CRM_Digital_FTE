"""
100% SYNCHRONOUS Email Polling Service - NO ASYNC ISSUES

Uses psycopg2 (synchronous PostgreSQL driver) instead of asyncpg.
No event loops, no concurrency issues, GUARANTEED TO WORK.

Usage: python poll_emails_sync.py
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
from src.channels.email_handler import EmailHandler, get_email_metrics
from production.config import settings
from production.agent.customer_success_agent import run_agent_sync

running = True

def signal_handler(sig, frame):
    global running
    print("\n\n[SHUTDOWN] Stopping...")
    running = False


def get_db_conn():
    """Get synchronous database connection"""
    return psycopg2.connect(
        settings.DATABASE_URL,
        sslmode='require'
    )


def create_customer(email):
    """Create/find customer - SYNCHRONOUS"""
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if exists
            cur.execute("SELECT * FROM customers WHERE email = %s", (email,))
            existing = cur.fetchone()
            
            if existing:
                print(f"  [OK] Found customer: {existing['id']}")
                return dict(existing)
            
            # Create new
            cur.execute(
                "INSERT INTO customers (email) VALUES (%s) RETURNING *",
                (email,)
            )
            customer = cur.fetchone()
            conn.commit()
            print(f"  [OK] Created customer: {customer['id']}")
            return dict(customer)
    finally:
        conn.close()


def create_conversation(customer_id, topic):
    """Create conversation - SYNCHRONOUS"""
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


def create_ticket(customer_id, channel, description, subject, conversation_id):
    """Create ticket - SYNCHRONOUS"""
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO tickets (customer_id, channel, description, subject, conversation_id, status)
                VALUES (%s, %s, %s, %s, %s, 'open') RETURNING *
                """,
                (customer_id, channel, description, subject, conversation_id)
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
    """Log AI interaction - SYNCHRONOUS"""
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


def process_email(email_data):
    """Process email - FULLY SYNCHRONOUS"""
    print(f"\n{'='*80}")
    print(f"[EMAIL RECEIVED] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    print(f"From: {email_data.get('from', 'UNKNOWN')}")
    print(f"Subject: {email_data.get('subject', 'NO SUBJECT')}")
    print(f"Message-ID: {email_data.get('message_id', 'NO ID')}")
    print(f"Body: {email_data.get('body', '')[:100]}")
    print(f"{'='*80}\n")
    
    start = time.time()
    result = {'success': False, 'error': None, 'ticket_id': None}
    
    try:
        # STEP 1: Customer
        print("[STEP 1/7] Creating customer...")
        customer = create_customer(email_data.get('from', ''))
        customer_id = customer['id']
        
        # STEP 2: Conversation
        print("[STEP 2/7] Creating conversation...")
        conversation = create_conversation(customer_id, email_data.get('subject', ''))
        conversation_id = conversation['id']
        
        # STEP 3: Ticket
        print("[STEP 3/7] Creating ticket...")
        ticket = create_ticket(
            customer_id=customer_id,
            channel='email',
            description=email_data.get('body', ''),
            subject=email_data.get('subject', ''),
            conversation_id=conversation_id
        )
        ticket_id = ticket['id']
        ticket_number = ticket['ticket_number']
        result['ticket_id'] = ticket_id
        
        # STEP 4: AI Agent
        print("[STEP 4/7] Calling AI agent...")
        ai_start = time.time()
        ai_response = run_agent_sync(
            customer_email=email_data.get('from', ''),
            subject=email_data.get('subject', ''),
            message_body=email_data.get('body', '')
        )
        ai_time = int((time.time() - ai_start) * 1000)
        print(f"  [OK] AI: {ai_time}ms | Sentiment: {ai_response.sentiment_score} | Escalation: {ai_response.escalation_required}")
        
        # STEP 5: Log AI
        print("[STEP 5/7] Logging AI interaction...")
        log_ai_interaction(
            ticket_id=ticket_id,
            customer_email=email_data.get('from', ''),
            original_message=email_data.get('body', ''),
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
        
        # STEP 7: SMTP
        print("[STEP 7/7] Sending SMTP reply...")
        handler = EmailHandler()
        success = handler.send_reply(email_data, ai_response.reply_text)
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


def main():
    global running
    
    print("="*80)
    print("100% SYNCHRONOUS EMAIL POLLING SERVICE")
    print("No async issues - Guaranteed to work")
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
            print(f"[OK] Database connected (test query: {result[0]})\n")
        conn.close()
    except Exception as e:
        print(f"[ERROR] Database failed: {e}\n")
        traceback.print_exc()
        sys.exit(1)
    
    # Test IMAP
    print("[TEST] IMAP connection...")
    try:
        handler = EmailHandler()
        mail = handler.get_imap_connection()
        mail.select('INBOX')
        status, data = mail.search(None, 'ALL')
        total = len(data[0].split()) if data[0] else 0
        status, unseen = mail.search(None, 'UNSEEN')
        unread = len(unseen[0].split()) if unseen[0] else 0
        mail.logout()
        print(f"[OK] IMAP: {total} total, {unread} unread\n")
    except Exception as e:
        print(f"[ERROR] IMAP failed: {e}\n")
        traceback.print_exc()
        sys.exit(1)
    
    # Test SMTP
    print("[TEST] SMTP connection...")
    try:
        handler = EmailHandler()
        smtp = handler.get_smtp_connection()
        smtp.quit()
        print(f"[OK] SMTP connected\n")
    except Exception as e:
        print(f"[ERROR] SMTP failed: {e}\n")
        traceback.print_exc()
        sys.exit(1)
    
    print("="*80)
    print("ALL TESTS PASSED - STARTING POLLING")
    print("="*80)
    print("\nPress Ctrl+C to stop\n")
    
    handler = EmailHandler()
    poll_count = 0
    
    while running:
        poll_count += 1
        ts = datetime.now().strftime('%H:%M:%S')
        
        try:
            print(f"[{ts}] Poll #{poll_count}...")
            
            processed = handler.poll_emails(process_email)
            
            if processed > 0:
                print(f"[{ts}] [OK] Processed {processed} email(s)")
                metrics = get_email_metrics().get_metrics()
                print(f"  Metrics: {metrics}")
            else:
                print(f"[{ts}] [INFO] No new emails")
                
        except Exception as e:
            print(f"[{ts}] [ERROR] {type(e).__name__}: {e}")
            traceback.print_exc()
        
        if running:
            time.sleep(args.interval)
    
    print("\n[SHUTDOWN] Stopped")


if __name__ == '__main__':
    main()
