"""
Find Recent Emails - Debug Script

Shows the 10 most recent emails in INBOX to help identify if your test email arrived.
"""
import imaplib
from datetime import datetime
from email import message_from_bytes
from production.config import settings

print("="*60)
print("FIND RECENT EMAILS")
print("="*60)

# Connect
mail = imaplib.IMAP4_SSL(settings.IMAP_HOST, settings.IMAP_PORT)
mail.login(settings.EMAIL_ADDRESS, settings.EMAIL_PASSWORD)
print(f"\n[OK] Logged in as {settings.EMAIL_ADDRESS}")

# Select INBOX
mail.select('INBOX')
print("[OK] INBOX selected\n")

# Search ALL emails (not just UNSEEN)
status, messages = mail.search(None, "ALL")
email_ids = messages[0].split()

print(f"Total emails in INBOX: {len(email_ids)}")
print(f"\nLast 10 emails (most recent first):\n")

# Get last 10 emails (most recent)
recent_ids = email_ids[-10:][::-1]  # Reverse to show newest first

for i, eid in enumerate(recent_ids, 1):
    status, msg_data = mail.fetch(eid, "(RFC822 FLAGS)")
    if status == 'OK':
        msg = message_from_bytes(msg_data[0][1])
        flags = msg_data[0][0].decode() if msg_data[0][0] else ""
        is_seen = "\\Seen" in flags
        
        print(f"{i}. {'[READ]' if is_seen else '[UNREAD]'}")
        print(f"   From: {msg.get('From', 'N/A')}")
        print(f"   Subject: {msg.get('Subject', 'N/A')}")
        print(f"   Date: {msg.get('Date', 'N/A')}")
        print(f"   Flags: {flags}")
        print()

# Now search UNSEEN specifically
print("="*60)
print("UNSEEN EMAILS SEARCH")
print("="*60)

status, messages = mail.search(None, "UNSEEN")
email_ids = messages[0].split()
print(f"Unread count: {len(email_ids)}")

if len(email_ids) > 0:
    print(f"\nFirst 5 unread emails:")
    for eid in email_ids[:5]:
        status, msg_data = mail.fetch(eid, "(RFC822)")
        if status == 'OK':
            msg = message_from_bytes(msg_data[0][1])
            print(f"  - From: {msg.get('From')[:50]} | Subject: {msg.get('Subject')[:50]}")

# Check for specific sender
print("\n" + "="*60)
print("SEARCH FOR YOUR TEST EMAIL")
print("="*60)
print("Looking for emails from your second Gmail account...")
print("(Enter the email address or press Enter to skip)")
test_email = input("Test email address: ").strip()

if test_email:
    status, messages = mail.search(None, f'FROM "{test_email}"')
    email_ids = messages[0].split()
    print(f"\nFound {len(email_ids)} email(s) from {test_email}")
    
    for eid in email_ids[:5]:
        status, msg_data = mail.fetch(eid, "(RFC822 FLAGS)")
        if status == 'OK':
            msg = message_from_bytes(msg_data[0][1])
            flags = msg_data[0][0].decode() if msg_data[0][0] else ""
            is_seen = "\\Seen" in flags
            print(f"  {'[READ]' if is_seen else '[UNREAD]'} {msg.get('Subject')}")

mail.logout()
print("\n[OK] Done")
