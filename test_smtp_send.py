"""
Quick SMTP Test - Send Test Email

This script tests SMTP connectivity and email sending without running the full poller.

Usage: python test_smtp_send.py
"""
from src.channels.email_handler import EmailHandler
from production.config import settings

print("="*60)
print("SMTP SEND TEST")
print("="*60)

print(f"\nConfiguration:")
print(f"  SMTP Host: {settings.SMTP_HOST}:{settings.SMTP_PORT}")
print(f"  Email: {settings.EMAIL_ADDRESS}")

# Test data
test_email = {
    'from': 'ahsenadil2@gmail.com',  # Your second account
    'subject': 'Test Subject',
    'message_id': '<test-message-id@example.com>'
}

test_body = """Dear Valued Customer,

This is a test email to verify SMTP is working correctly.

If you receive this, the SMTP configuration is correct!

Best regards,
Digital FTE System
"""

print(f"\nTest Details:")
print(f"  To: {test_email['from']}")
print(f"  Subject: Re: {test_email['subject']}")

print(f"\n{'='*60}")
print("SENDING TEST EMAIL...")
print(f"{'='*60}\n")

try:
    handler = EmailHandler()
    
    print("[TEST] Creating email handler...")
    print("[TEST] Calling send_reply()...\n")
    
    success = handler.send_reply(test_email, test_body)
    
    print(f"\n{'='*60}")
    if success:
        print("✅ SUCCESS! Email sent via SMTP")
        print(f"   Check inbox of: {test_email['from']}")
        print(f"   Subject: Re: {test_email['subject']}")
    else:
        print("❌ FAILED! send_reply() returned False")
    print(f"{'='*60}")
    
except Exception as e:
    print(f"\n{'='*60}")
    print(f"❌ ERROR: {type(e).__name__}")
    print(f"   Message: {str(e)}")
    print(f"{'='*60}")
    import traceback
    traceback.print_exc()

print(f"\n{'='*60}")
print("TEST COMPLETE")
print(f"{'='*60}")
