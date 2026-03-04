"""
Mark All Emails as Read

This script marks all unread emails in INBOX as read,
so you can test the polling system with fresh emails.

Usage: python mark_all_read.py
"""
import imaplib
from production.config import settings

print("="*60)
print("MARK ALL GMAIL EMAILS AS READ")
print("="*60)

print(f"\nConnecting to Gmail IMAP...")
print(f"Account: {settings.EMAIL_ADDRESS}")

# Connect
mail = imaplib.IMAP4_SSL(settings.IMAP_HOST, settings.IMAP_PORT)
mail.login(settings.EMAIL_ADDRESS, settings.EMAIL_PASSWORD)
print("[OK] Connected and logged in\n")

# Select INBOX
mail.select('INBOX')
print("INBOX selected\n")

# Search for UNSEEN
print("Searching for UNSEEN emails...")
status, messages = mail.search(None, "UNSEEN")
email_ids = messages[0].split()

print(f"Found {len(email_ids)} unread email(s)")

if len(email_ids) == 0:
    print("\n[INFO] No unread emails to mark as read!")
    print("Your inbox is already all read.")
else:
    # Mark all as read in batches of 50
    print(f"\nMarking all {len(email_ids)} emails as read (in batches of 50)...")
    
    batch_size = 50
    marked_count = 0
    
    for i in range(0, len(email_ids), batch_size):
        batch = email_ids[i:i+batch_size]
        batch_ids = b','.join(batch)
        
        status, result = mail.store(batch_ids, "+FLAGS", "\\Seen")
        
        if status == 'OK':
            marked_count += len(batch)
            print(f"  Marked batch {i//batch_size + 1}: {len(batch)} emails")
        else:
            print(f"  [ERROR] Batch {i//batch_size + 1} failed: {result}")
    
    print(f"\n[OK] Marked {marked_count}/{len(email_ids)} emails as read")

# Verify
print("\nVerifying...")
status, messages = mail.search(None, "UNSEEN")
remaining = messages[0].split()
print(f"Remaining unread emails: {len(remaining)}")

# Cleanup
mail.logout()
print("\n[OK] Done!")

print("\n" + "="*60)
print("NEXT STEPS:")
print("1. Send a test email to", settings.EMAIL_ADDRESS)
print("2. Run: python poll_emails.py")
print("3. The new email should be detected!")
print("="*60)
