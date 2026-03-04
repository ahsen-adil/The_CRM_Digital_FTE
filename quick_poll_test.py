"""Quick 10-second poll test"""
import signal
import sys
import time
from datetime import datetime
from src.channels.email_handler import EmailHandler

running = True

def signal_handler(sig, frame):
    global running
    print("\nStopping...")
    running = False

signal.signal(signal.SIGINT, signal_handler)

def process(email):
    print(f"\n[EMAIL] From: {email['from']} | Subject: {email['subject']}")
    return {'ticket_id': 'TEST'}

handler = EmailHandler()
interval = 10  # 10 seconds for quick test

print("Quick test - polling every 10 seconds")
print("Press Ctrl+C to stop\n")

count = 0
while running and count < 6:  # Max 6 polls = 1 minute
    count += 1
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Poll #{count}...")
    processed = handler.poll_emails(process)
    print(f"  Found: {processed} emails")
    if running:
        time.sleep(interval)

print("\nTest complete")
