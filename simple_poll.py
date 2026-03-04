"""
Simple Email Polling Test (No Database)

Quick test to continuously poll emails without database dependencies.

Usage:
    python simple_poll.py
    
Press Ctrl+C to stop
"""
import signal
import sys
import time
from datetime import datetime
from src.channels.email_handler import EmailHandler, get_email_metrics


# Global flag for graceful shutdown
running = True


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global running
    print("\n\n[INFO] Stopping...")
    running = False


def simple_process(email_data):
    """Simple email processor"""
    print(f"\n{'='*60}")
    print(f"[NEW EMAIL] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    print(f"From: {email_data.get('from', 'Unknown')}")
    print(f"Subject: {email_data.get('subject', 'No subject')}")
    print(f"\nBody:")
    print(f"  {email_data.get('body', '')[:300]}")
    print(f"{'='*60}")
    
    return {
        'ticket_id': 'TEST-001',
        'sentiment_score': 0.8,
        'escalation_triggered': False
    }


def main():
    """Main polling loop"""
    global running
    
    # Setup signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("="*60)
    print("EMAIL POLLING TEST (Simple Mode)")
    print("="*60)
    
    handler = EmailHandler()
    interval = 60  # seconds
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


if __name__ == '__main__':
    main()
