"""
DEBUG: Email Polling with Verbose IMAP Logging

This version shows detailed IMAP debug information to diagnose email detection issues.

Run: python debug_poll.py
"""
import imaplib
import signal
import sys
import time
from datetime import datetime
from production.config import settings

# Global flag
running = True

def signal_handler(sig, frame):
    global running
    print("\n\n[INFO] Stopping...")
    running = False

signal.signal(signal.SIGINT, signal_handler)

print("="*60)
print("EMAIL IMAP DEBUG TEST")
print("="*60)

# Step 1: Show configuration
print("\n[STEP 1] Configuration Check")
print(f"  EMAIL_ADDRESS: {settings.EMAIL_ADDRESS}")
print(f"  IMAP_HOST: {settings.IMAP_HOST}")
print(f"  IMAP_PORT: {settings.IMAP_PORT}")

# Step 2: Connect to IMAP
print("\n[STEP 2] Connecting to IMAP...")
try:
    mail = imaplib.IMAP4_SSL(settings.IMAP_HOST, settings.IMAP_PORT)
    print(f"  [OK] Connected to {settings.IMAP_HOST}:{settings.IMAP_PORT}")
except Exception as e:
    print(f"  [ERROR] Connection failed: {e}")
    sys.exit(1)

# Step 3: Login
print("\n[STEP 3] Logging in...")
try:
    mail.login(settings.EMAIL_ADDRESS, settings.EMAIL_PASSWORD)
    print(f"  [OK] Logged in as {settings.EMAIL_ADDRESS}")
except Exception as e:
    print(f"  [ERROR] Login failed: {e}")
    print("  HINT: Check if you're using Gmail App Password, not regular password")
    sys.exit(1)

# Step 4: List all folders
print("\n[STEP 4] Listing IMAP folders...")
try:
    status, folders = mail.list()
    print(f"  [OK] Found {len(folders)} folders:")
    for folder in folders[:10]:  # Show first 10
        folder_name = folder.decode().split(' "/" ')[-1]
        print(f"    - {folder_name}")
    if len(folders) > 10:
        print(f"    ... and {len(folders) - 10} more")
except Exception as e:
    print(f"  [ERROR] Failed to list folders: {e}")

# Step 5: Select INBOX
print("\n[STEP 5] Selecting INBOX...")
try:
    status, messages = mail.select('INBOX')
    print(f"  Status: {status}")
    if status == 'OK':
        print(f"  [OK] INBOX selected")
        # Get total message count
        status, count = mail.status('INBOX', 'MESSAGES')
        if status == 'OK':
            print(f"  Total messages in INBOX: {count[0].decode()}")
        
        # Get unread count
        status, count = mail.status('INBOX', 'UNSEEN')
        if status == 'OK':
            print(f"  Unread (UNSEEN) messages: {count[0].decode()}")
    else:
        print(f"  [ERROR] Failed to select INBOX: {messages}")
except Exception as e:
    print(f"  [ERROR] {e}")

# Step 6: Search for UNSEEN emails
print("\n[STEP 6] Searching for UNSEEN emails...")
try:
    status, messages = mail.search(None, "UNSEEN")
    print(f"  Search Status: {status}")
    print(f"  Raw response: {messages}")
    
    if status == 'OK':
        email_ids = messages[0].split()
        print(f"  Number of unread emails: {len(email_ids)}")
        
        if email_ids:
            print(f"  Email IDs: {email_ids[:10]}")  # Show first 10
            
            # Fetch first email as test
            print(f"\n[STEP 7] Fetching first unread email...")
            eid = email_ids[0]
            status, msg_data = mail.fetch(eid, "(RFC822)")
            print(f"  Fetch Status: {status}")
            
            if status == 'OK':
                print(f"  [OK] Email fetched successfully")
                print(f"  Raw data length: {len(msg_data[0][1])} bytes")
                
                # Parse basic headers
                from email import message_from_bytes
                msg = message_from_bytes(msg_data[0][1])
                print(f"\n  Email Details:")
                print(f"    From: {msg.get('From', 'N/A')}")
                print(f"    To: {msg.get('To', 'N/A')}")
                print(f"    Subject: {msg.get('Subject', 'N/A')}")
                print(f"    Date: {msg.get('Date', 'N/A')}")
                print(f"    Message-ID: {msg.get('Message-ID', 'N/A')}")
                
                # Check if it has body
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True)
                            if body:
                                body_str = body.decode('utf-8', errors='ignore')
                                print(f"    Body length: {len(body_str)} chars")
                                print(f"    Body preview: {body_str[:100]}...")
                            break
                else:
                    if msg.get_content_type() == "text/plain":
                        body = msg.get_payload(decode=True)
                        if body:
                            body_str = body.decode('utf-8', errors='ignore')
                            print(f"    Body length: {len(body_str)} chars")
                            print(f"    Body preview: {body_str[:100]}...")
        else:
            print(f"  [INFO] No unread emails found!")
            print(f"\n  TROUBLESHOOTING TIPS:")
            print(f"    1. Send a test email to {settings.EMAIL_ADDRESS}")
            print(f"    2. Check if email went to Spam folder")
            print(f"    3. Make sure email is actually unread (not opened in Gmail)")
            print(f"    4. Gmail may delay IMAP sync by a few minutes")
            
except Exception as e:
    print(f"  [ERROR] Search failed: {e}")
    import traceback
    traceback.print_exc()

# Step 8: Check other folders
print("\n[STEP 8] Checking other common folders...")
for folder_name in ['INBOX', '[Gmail]/All Mail', 'Spam', 'Trash']:
    try:
        status, messages = mail.select(folder_name)
        if status == 'OK':
            status, unseen = mail.status(folder_name, 'UNSEEN')
            if status == 'OK':
                unseen_count = len(unseen[0].split(b' ')) if unseen[0] else 0
                print(f"  {folder_name}: {unseen_count} unseen")
    except:
        pass

# Cleanup
print("\n[STEP 9] Closing connection...")
try:
    mail.close()
except:
    pass  # Ignore if not in SELECTED state
mail.logout()
print("[OK] Disconnected")

print("\n" + "="*60)
print("DEBUG TEST COMPLETE")
print("="*60)
