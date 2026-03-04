"""
Simple Email Polling Test - Synchronous Version
No asyncio conflicts - uses direct sync database calls.
"""
import signal
import sys
import time
from datetime import datetime
from src.channels.email_handler import EmailHandler, get_email_metrics

print("="*60)
print("SIMPLE EMAIL POLLING TEST")
print("="*60)

# Global flag
running = True

def signal_handler(sig, frame):
    global running
    print("\n\n[INFO] Stopping...")
    running = False

signal.signal(signal.SIGINT, signal_handler)

def simple_process(email_data):
    """Simple processor - just logs, no database"""
    print(f"\n{'='*60}")
    print(f"[EMAIL RECEIVED] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    print(f"From: {email_data.get('from', 'Unknown')}")
    print(f"Subject: {email_data.get('subject', 'No subject')}")
    print(f"Message-ID: {email_data.get('message_id', 'N/A')}")
    
    body = email_data.get('body', '')
    print(f"\nBody:")
    print(f"  {body[:300]}")
    print(f"{'='*60}")
    
    # Just return success without DB calls
    return {
        'ticket_id': 'TEST-001',
        'sentiment_score': 0.8,
        'escalation_triggered': False,
        'response_sent': True
    }

# Main loop
handler = EmailHandler()
interval = 30  # 30 seconds for testing
poll_count = 0

print(f"\nPolling every {interval} seconds...")
print("Press Ctrl+C to stop\n")

while running:
    poll_count += 1
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    try:
        print(f"[{timestamp}] Poll #{poll_count}...")
        
        # Poll for emails
        processed = handler.poll_emails(simple_process)
        
        if processed > 0:
            metrics = get_email_metrics().get_metrics()
            print(f"  Processed: {processed} emails")
            print(f"  Total processed this session: {metrics['emails_processed']}")
        else:
            print(f"  No new emails")
            
    except Exception as e:
        print(f"  Error: {e}")
    
    # Wait for next poll
    if running:
        time.sleep(interval)

# Show final metrics
metrics = get_email_metrics().get_metrics()
print(f"\n[FINAL METRICS]")
print(f"  Emails Processed: {metrics['emails_processed']}")
print(f"  Escalations: {metrics['escalations_triggered']}")
print(f"  Errors: {metrics['processing_errors']}")
print("\nStopped.")
