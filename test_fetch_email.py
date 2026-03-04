"""Quick Email Fetch Test"""
from src.channels.email_handler import EmailHandler

print('Fetching unread emails...')
handler = EmailHandler()

try:
    emails = handler.get_unread_emails()
    print(f'Found {len(emails)} unread emails')
    
    if emails:
        print(f'\nFirst email:')
        print(f'  Subject: {emails[0].get("subject")}')
        print(f'  From: {emails[0].get("from")}')
        print(f'  Message-ID: {emails[0].get("message_id")}')
        print(f'  Body (first 100 chars): {emails[0].get("body", "")[:100]}')
except Exception as e:
    print(f'Error: {e}')
