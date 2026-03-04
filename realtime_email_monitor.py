"""
Real-time Email Monitor - Watches for NEW emails as they arrive

This script monitors Gmail in real-time to catch emails BEFORE they get marked as read.
"""
import imaplib
import time
from datetime import datetime
from email import message_from_bytes

EMAIL_ADDRESS = "meoahsan01@gmail.com"
EMAIL_PASSWORD = "jezq yboz rbmv eknm"  # Gmail App Password

print("="*60)
print("REAL-TIME EMAIL MONITOR")
print("="*60)
print(f"Monitoring: {EMAIL_ADDRESS}")
print("Watching for NEW emails as they arrive...\n")

# Connect
mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
mail.select("INBOX")

print("[OK] Connected to Gmail IMAP\n")

# Get initial state
status, data = mail.search(None, "ALL")
initial_count = len(data[0].split()) if data[0] else 0
print(f"Initial email count: {initial_count}")
print(f"Watching for new emails (Ctrl+C to stop)...\n")

last_count = initial_count
check_count = 0

try:
    while True:
        check_count += 1
        mail.select("INBOX")  # Refresh
        
        # Check ALL emails
        status, data = mail.search(None, "ALL")
        all_emails = data[0].split()
        current_count = len(all_emails)
        
        # Check UNSEEN emails
        status, unseen_data = mail.search(None, "UNSEEN")
        unseen_emails = unseen_data[0].split()
        unseen_count = len(unseen_emails)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Show status every 5 checks
        if check_count % 5 == 0:
            print(f"[{timestamp}] Check #{check_count}: Total={current_count}, Unseen={unseen_count}")
        
        # Detect new emails
        if current_count > last_count:
            new_count = current_count - last_count
            print(f"\n{'='*60}")
            print(f"[{timestamp}] 📬 NEW EMAIL DETECTED! ({new_count} email(s))")
            print(f"{'='*60}")
            print(f"Total emails: {current_count}")
            print(f"Unseen emails: {unseen_count}")
            
            # Fetch the newest email
            if all_emails:
                newest_id = all_emails[-1]
                status, msg_data = mail.fetch(newest_id, "(RFC822 FLAGS)")
                
                if status == "OK":
                    msg = message_from_bytes(msg_data[0][1])
                    flags = msg_data[0][0].decode() if msg_data[0][0] else ""
                    
                    print(f"\nNewest Email Details:")
                    print(f"  ID: {newest_id.decode()}")
                    print(f"  From: {msg.get('From', 'N/A')}")
                    print(f"  Subject: {msg.get('Subject', 'N/A')}")
                    print(f"  Date: {msg.get('Date', 'N/A')}")
                    print(f"  Flags: {flags}")
                    print(f"  Is UNSEEN: {'\\Seen' not in flags}")
                    
                    # Check if it's already marked as read
                    if '\\Seen' in flags:
                        print(f"\n⚠️  WARNING: Email is already marked as READ!")
                        print(f"    This means Gmail auto-marked it as read.")
                        print(f"    Possible causes:")
                        print(f"    1. Email opened in Gmail web interface")
                        print(f"    2. Gmail 'Mark as read' setting enabled")
                        print(f"    3. Another email client marked it read")
                    else:
                        print(f"\n✅ Email is UNREAD - ready for processing!")
            
            print(f"{'='*60}\n")
            last_count = current_count
        
        # Check for unseen specifically
        if unseen_count > 0 and unseen_emails:
            print(f"\n{'='*60}")
            print(f"[{timestamp}] 📬 UNSEEN EMAIL(S) FOUND: {unseen_count}")
            print(f"{'='*60}")
            
            # Show first unseen email
            status, msg_data = mail.fetch(unseen_emails[0], "(RFC822 FLAGS)")
            if status == "OK":
                msg = message_from_bytes(msg_data[0][1])
                print(f"  From: {msg.get('From', 'N/A')}")
                print(f"  Subject: {msg.get('Subject', 'N/A')}")
            
            print(f"{'='*60}\n")
        
        time.sleep(3)  # Check every 3 seconds
        
except KeyboardInterrupt:
    print("\n\n[INFO] Stopping monitor...")
    mail.logout()
    print("[OK] Disconnected")
