"""
Email MVP Connectivity and Integration Test
Tests IMAP, SMTP, Database, and full email processing flow
"""
import asyncio
import sys
import os

# Fix Windows console encoding
os.system('chcp 65001 > nul')
sys.stdout.reconfigure(encoding='utf-8')

print('='*60)
print('EMAIL MVP CONNECTIVITY TEST')
print('='*60)

# Test 1: IMAP Connection
print('\n[TEST 1] IMAP Connection...')
try:
    from src.channels.email_handler import EmailHandler, get_email_metrics
    handler = EmailHandler()
    mail = handler.get_imap_connection()
    print('[OK] IMAP Connected to imap.gmail.com:993')
    mail.select('INBOX')
    status, messages = mail.search(None, 'UNSEEN')
    unread_count = len(messages[0].split()) if messages[0] else 0
    print(f'[OK] Found {unread_count} unread email(s)')
    mail.logout()
    print('[OK] IMAP Disconnected')
except Exception as e:
    print(f'[ERROR] IMAP Error: {e}')

# Test 2: SMTP Connection
print('\n[TEST 2] SMTP Connection...')
try:
    handler = EmailHandler()
    server = handler.get_smtp_connection()
    print('[OK] SMTP Connected to smtp.gmail.com:587')
    server.quit()
    print('[OK] SMTP Disconnected')
except Exception as e:
    print(f'[ERROR] SMTP Error: {e}')

# Test 3: Database Connection
print('\n[TEST 3] Database Connection...')
try:
    from production.database.queries import db_pool
    
    async def test_db():
        await db_pool.create_pool()
        print('[OK] Database Connected to Neon PostgreSQL')
        result = await db_pool.fetchval('SELECT 1')
        print(f'[OK] Database Query Test: {result}')
        await db_pool.close_pool()
        print('[OK] Database Disconnected')
    
    asyncio.run(test_db())
except Exception as e:
    print(f'[ERROR] Database Error: {e}')

# Test 4: Metrics Counter
print('\n[TEST 4] Metrics Counter...')
try:
    metrics = get_email_metrics()
    print(f'[OK] Metrics Available: {metrics.get_metrics()}')
    metrics.increment_emails_processed()
    metrics.increment_escalations_triggered()
    print(f'[OK] After Increment: {metrics.get_metrics()}')
except Exception as e:
    print(f'[ERROR] Metrics Error: {e}')

# Test 5: Email Polling (with mock callback)
print('\n[TEST 5] Email Polling Test...')
try:
    def mock_callback(email_data):
        print(f'   Processing: {email_data.get("subject", "No subject")}')
        print(f'      From: {email_data.get("from", "Unknown")}')
        return {
            'ticket_id': 'TEST-123',
            'sentiment_score': 0.75,
            'escalation_triggered': False
        }
    
    handler = EmailHandler()
    processed = handler.poll_emails(mock_callback)
    print(f'[OK] Processed {processed} email(s)')
    
    # Show final metrics
    final_metrics = get_email_metrics().get_metrics()
    print(f'\nFINAL METRICS:')
    print(f'   Emails Processed: {final_metrics["emails_processed"]}')
    print(f'   Escalations Triggered: {final_metrics["escalations_triggered"]}')
    print(f'   Processing Errors: {final_metrics["processing_errors"]}')
    print(f'   Duplicate Emails Blocked: {final_metrics["duplicate_emails_blocked"]}')
except Exception as e:
    print(f'[ERROR] Polling Error: {e}')

print('\n' + '='*60)
print('EMAIL MVP TEST COMPLETE')
print('='*60)
