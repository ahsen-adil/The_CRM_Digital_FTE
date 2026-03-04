"""
Complete Email MVP Test
Tests: IMAP, SMTP, Database, Email Polling, Metrics, Observability
"""
import asyncio
from src.channels.email_handler import EmailHandler, get_email_metrics
from production.database.queries import db_pool

print('='*60)
print('EMAIL MVP COMPLETE TEST')
print('='*60)

# TEST 1: IMAP
print('\n[TEST 1/5] IMAP Connection...')
try:
    handler = EmailHandler()
    mail = handler.get_imap_connection()
    mail.select('INBOX')
    status, messages = mail.search(None, 'UNSEEN')
    unread = len(messages[0].split()) if messages[0] else 0
    mail.logout()
    print(f'  [PASS] IMAP connected - {unread} unread emails')
except Exception as e:
    print(f'  [FAIL] {e}')

# TEST 2: SMTP
print('\n[TEST 2/5] SMTP Connection...')
try:
    handler = EmailHandler()
    server = handler.get_smtp_connection()
    server.quit()
    print('  [PASS] SMTP connected')
except Exception as e:
    print(f'  [FAIL] {e}')

# TEST 3: Database
print('\n[TEST 3/5] Database Connection...')
async def test_db():
    try:
        await db_pool.create_pool()
        result = await db_pool.fetchval('SELECT 1')
        print(f'  [PASS] Database connected - Query result: {result}')
        await db_pool.close_pool()
    except Exception as e:
        print(f'  [FAIL] {e}')

asyncio.run(test_db())

# TEST 4: Metrics
print('\n[TEST 4/5] Metrics Counter...')
try:
    metrics = get_email_metrics()
    initial = metrics.get_metrics()
    print(f'  Initial: {initial}')
    metrics.increment_emails_processed()
    metrics.increment_escalations_triggered()
    updated = metrics.get_metrics()
    print(f'  After increment: {updated}')
    print('  [PASS] Metrics working')
except Exception as e:
    print(f'  [FAIL] {e}')

# TEST 5: Email Polling with Observability
print('\n[TEST 5/5] Email Polling with Observability...')
try:
    def process_email(email_data):
        """Simulate email processing callback"""
        print(f'    Processing: {email_data.get("subject", "No subject")[:50]}')
        print(f'    From: {email_data.get("from", "Unknown")}')
        return {
            'ticket_id': 'TEST-123',
            'sentiment_score': 0.75,
            'escalation_triggered': False
        }
    
    handler = EmailHandler()
    processed = handler.poll_emails(process_email)
    print(f'  [PASS] Processed {processed} emails')
    
    # Show metrics
    final = get_email_metrics().get_metrics()
    print(f'\n  METRICS SUMMARY:')
    print(f'    Emails Processed: {final["emails_processed"]}')
    print(f'    Escalations: {final["escalations_triggered"]}')
    print(f'    Errors: {final["processing_errors"]}')
    print(f'    Duplicates Blocked: {final["duplicate_emails_blocked"]}')
except Exception as e:
    print(f'  [FAIL] {e}')

print('\n' + '='*60)
print('ALL TESTS COMPLETE')
print('='*60)
