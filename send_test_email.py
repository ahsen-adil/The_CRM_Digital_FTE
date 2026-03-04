"""
Send a test email to verify the polling system works.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Email configuration
FROM_EMAIL = "ahsenadil2@gmail.com"
FROM_PASSWORD = "your_app_password_here"  # You'll need to enter this
TO_EMAIL = "meoahsan01@gmail.com"
SUBJECT = "TEST AI AGENT - Automated Test"
BODY = """Hi,

This is an automated test email to verify the AI Customer Success Agent is working correctly.

Can you please help me understand how to create my first project in CloudManage? I need step-by-step instructions.

Thanks,
Automated Test System
"""

print("="*60)
print("SENDING TEST EMAIL")
print("="*60)
print(f"From: {FROM_EMAIL}")
print(f"To: {TO_EMAIL}")
print(f"Subject: {SUBJECT}")
print()

try:
    # Create message
    msg = MIMEMultipart()
    msg['From'] = FROM_EMAIL
    msg['To'] = TO_EMAIL
    msg['Subject'] = SUBJECT
    msg.attach(MIMEText(BODY, 'plain', 'utf-8'))
    
    # Connect and send
    print("[INFO] Connecting to Gmail SMTP...")
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    print(f"[INFO] Logging in as {FROM_EMAIL}...")
    server.login(FROM_EMAIL, FROM_PASSWORD)
    print("[INFO] Sending email...")
    server.sendmail(FROM_EMAIL, TO_EMAIL, msg.as_string())
    print("[INFO] Email sent successfully!")
    server.quit()
    
    print()
    print("="*60)
    print("✅ TEST EMAIL SENT")
    print("="*60)
    print()
    print("Now watch the poll_emails.py output - within 60 seconds")
    print("you should see the email being detected and processed!")
    
except Exception as e:
    print(f"\n{'='*60}")
    print(f"❌ FAILED TO SEND EMAIL")
    print(f"{'='*60}")
    print(f"Error: {type(e).__name__}: {e}")
    print()
    print("Make sure you've set FROM_PASSWORD to your Gmail App Password")
    import traceback
    traceback.print_exc()
