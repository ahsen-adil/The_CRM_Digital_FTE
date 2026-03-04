---
name: email-integration
description: Use this skill whenever the user wants to integrate email into a CRM or automation system using Python with SMTP and IMAP — without Gmail API or OAuth2. Trigger this skill when the user wants to send emails via SMTP, read emails via IMAP, auto-reply to customer queries, build an email bot using username/password login, or use any email provider (Gmail, Outlook, Yahoo, custom SMTP server) programmatically. Also trigger when the user mentions smtplib, imaplib, SMTP, IMAP, email automation without API, or app passwords for Gmail.
---

# SMTP/IMAP Email Integration SKILL

## Overview
This skill covers sending and receiving emails using Python's built-in `smtplib` and `imaplib` libraries — **no API keys, no OAuth2, no Google Cloud Console required**. Just an email address and password (or App Password).

Works with: **Gmail, Outlook, Yahoo, Zoho, custom SMTP servers**

## 1. Environment Variables (.env)

```env
EMAIL_ADDRESS=yourname@gmail.com
EMAIL_PASSWORD=abcd efgh ijkl mnop
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
POLL_INTERVAL=60
```

> Add `.env` to your `.gitignore` — never commit credentials.

---

## 2. Config (config.py)

```python
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_ADDRESS  = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_HOST      = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT      = int(os.getenv("SMTP_PORT", 587))
IMAP_HOST      = os.getenv("IMAP_HOST", "imap.gmail.com")
IMAP_PORT      = int(os.getenv("IMAP_PORT", 993))
POLL_INTERVAL  = int(os.getenv("POLL_INTERVAL", 60))
```

Install dotenv:
```bash
pip install python-dotenv
```

---

## 3. Read Emails via IMAP (imap_reader.py)

```python
import imaplib
import email
from email.header import decode_header
from config import EMAIL_ADDRESS, EMAIL_PASSWORD, IMAP_HOST, IMAP_PORT


def get_imap_connection():
    """Connect and login to IMAP server."""
    mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    return mail


def get_unread_emails():
    """Fetch all unread emails from inbox."""
    mail = get_imap_connection()
    mail.select("INBOX")

    # Search for unread emails
    status, messages = mail.search(None, "UNSEEN")
    email_ids = messages[0].split()

    emails = []
    for eid in email_ids:
        status, msg_data = mail.fetch(eid, "(RFC822)")
        raw_email = msg_data[0][1]
        parsed = parse_email(raw_email, eid)
        if parsed:
            emails.append(parsed)

    mail.logout()
    return emails


def decode_str(value):
    """Decode encoded email header strings."""
    decoded, encoding = decode_header(value)[0]
    if isinstance(decoded, bytes):
        return decoded.decode(encoding or "utf-8", errors="ignore")
    return decoded


def parse_email(raw_email: bytes, email_id) -> dict:
    """Parse raw email bytes into a structured dict."""
    msg = email.message_from_bytes(raw_email)

    subject = decode_str(msg.get("Subject", ""))
    from_addr = decode_str(msg.get("From", ""))
    to_addr = decode_str(msg.get("To", ""))
    message_id = msg.get("Message-ID", "")
    references = msg.get("References", "")
    in_reply_to = msg.get("In-Reply-To", "")

    body = extract_body(msg)

    return {
        "email_id": email_id,
        "subject": subject,
        "from": from_addr,
        "to": to_addr,
        "message_id": message_id,
        "references": references,
        "in_reply_to": in_reply_to,
        "body": body,
    }


def extract_body(msg) -> str:
    """Extract plain text body from email (handles multipart)."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                charset = part.get_content_charset() or "utf-8"
                return part.get_payload(decode=True).decode(charset, errors="ignore")
    else:
        if msg.get_content_type() == "text/plain":
            charset = msg.get_content_charset() or "utf-8"
            return msg.get_payload(decode=True).decode(charset, errors="ignore")
    return ""


def mark_as_read(email_id):
    """Mark an email as read (seen) by its IMAP ID."""
    mail = get_imap_connection()
    mail.select("INBOX")
    mail.store(email_id, "+FLAGS", "\\Seen")
    mail.logout()
```

---

## 4. Send Reply via SMTP (smtp_sender.py)

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import EMAIL_ADDRESS, EMAIL_PASSWORD, SMTP_HOST, SMTP_PORT


def send_reply(email_data: dict, reply_body: str):
    """
    Send a reply email in the same thread.
    Uses In-Reply-To and References headers for proper threading.
    """
    msg = MIMEMultipart()
    msg["From"]    = EMAIL_ADDRESS
    msg["To"]      = email_data["from"]
    msg["Subject"] = f"Re: {email_data['subject']}"

    # Threading headers (RFC 2822)
    msg["In-Reply-To"] = email_data["message_id"]

    references = email_data.get("references", "")
    if references:
        msg["References"] = f"{references} {email_data['message_id']}"
    else:
        msg["References"] = email_data["message_id"]

    # Attach plain text body
    msg.attach(MIMEText(reply_body, "plain"))

    # Connect and send
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()              # Encrypt connection
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(
            EMAIL_ADDRESS,
            email_data["from"],
            msg.as_string()
        )

    print(f"Reply sent → {email_data['from']} | Subject: {email_data['subject']}")


def send_new_email(to: str, subject: str, body: str):
    """Send a brand new email (not a reply)."""
    msg = MIMEMultipart()
    msg["From"]    = EMAIL_ADDRESS
    msg["To"]      = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, to, msg.as_string())

    print(f"Email sent → {to} | Subject: {subject}")
```

---

## 5. CRM Reply Logic (crm_handler.py)

```python
from config import EMAIL_ADDRESS


def generate_reply(email_data: dict) -> str:
    """
    Route incoming email to the right reply template
    based on subject and body keywords.
    """
    subject = email_data["subject"].lower()
    body    = email_data["body"].lower()
    name    = extract_name(email_data["from"])

    # Skip emails sent by yourself
    if EMAIL_ADDRESS in email_data["from"]:
        return None

    # Keyword routing
    if any(w in body or w in subject for w in ["price", "pricing", "cost", "quote", "plan"]):
        return pricing_reply(name)

    elif any(w in body or w in subject for w in ["support", "help", "issue", "problem", "bug", "error"]):
        return support_reply(name)

    elif any(w in body or w in subject for w in ["demo", "trial", "free trial", "walkthrough"]):
        return demo_reply(name)

    elif any(w in body or w in subject for w in ["invoice", "payment", "billing", "refund"]):
        return billing_reply(name)

    else:
        return default_reply(name)


def extract_name(from_header: str) -> str:
    """Extract first name from 'John Doe <[email protected]>' format."""
    if "<" in from_header:
        name = from_header.split("<")[0].strip().strip('"')
        return name.split()[0] if name else "there"
    return "there"


# --- Reply Templates ---

def pricing_reply(name: str) -> str:
    return f"""Hi {name},

Thank you for your interest!

Our pricing plans:
- Starter: $29/month (up to 5 users)
- Pro: $79/month (up to 20 users)
- Enterprise: Custom pricing

Book a call to discuss your needs: https://calendly.com/yourcompany/pricing

Best regards,
Sales Team
Your Company"""


def support_reply(name: str) -> str:
    return f"""Hi {name},

Thank you for reaching out to our support team!

We have received your query and will respond within 24 hours.
For urgent issues, visit our help center: https://help.yourcompany.com

Ticket ID: #{generate_ticket_id()}

Best regards,
Support Team
Your Company"""


def demo_reply(name: str) -> str:
    return f"""Hi {name},

We'd love to show you what we can do!

Book a free 30-minute demo here: https://calendly.com/yourcompany/demo

We'll walk you through everything and answer all your questions live.

Best regards,
Sales Team
Your Company"""


def billing_reply(name: str) -> str:
    return f"""Hi {name},

Thank you for contacting our billing team.

For invoice and payment queries, please email: billing@yourcompany.com
Or login to your account: https://app.yourcompany.com/billing

We'll get back to you within 1 business day.

Best regards,
Billing Team
Your Company"""


def default_reply(name: str) -> str:
    return f"""Hi {name},

Thank you for your email!

We have received your message and will get back to you within 1 business day.

Best regards,
Your Company Team"""


import random
import string

def generate_ticket_id() -> str:
    """Generate a simple random ticket ID."""
    return "".join(random.choices(string.digits, k=6))
```

---

## 6. Main Polling Loop (main.py)

```python
import time
from imap_reader import get_unread_emails, mark_as_read
from smtp_sender import send_reply
from crm_handler import generate_reply
from config import POLL_INTERVAL


def process_emails():
    """Read unread emails, auto-reply, mark as read."""
    print("Checking inbox...")
    emails = get_unread_emails()

    if not emails:
        print("No new emails.\n")
        return

    for email_data in emails:
        print(f"New email from: {email_data['from']}")
        print(f"Subject: {email_data['subject']}")

        # Generate reply
        reply = generate_reply(email_data)

        if reply is None:
            print("Skipping (sent by self)\n")
            mark_as_read(email_data["email_id"])
            continue

        # Send reply
        send_reply(email_data, reply)

        # Mark as read so it won't be processed again
        mark_as_read(email_data["email_id"])
        print("Done.\n")


def main():
    print(f"SMTP CRM Bot started. Polling every {POLL_INTERVAL} seconds...")
    while True:
        try:
            process_emails()
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
```

---

## 7. Run on a Server (systemd service)

To keep the bot running 24/7 on a Linux server:

```ini
# /etc/systemd/system/smtp-crm.service

[Unit]
Description=SMTP CRM Email Bot
After=network.target

[Service]
WorkingDirectory=/path/to/smtp-crm
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable smtp-crm
sudo systemctl start smtp-crm
sudo systemctl status smtp-crm
```

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `SMTPAuthenticationError` | Wrong password or App Password not used | Generate App Password for Gmail |
| `IMAP LOGIN failed` | IMAP not enabled | Enable IMAP in Gmail Settings → Forwarding & POP/IMAP |
| Emails not threading | Missing `In-Reply-To` / `References` headers | Ensure both headers are set in `smtp_sender.py` |
| Replying to own emails | No self-check | Add `EMAIL_ADDRESS in email_data["from"]` check |
| `Connection refused` | Wrong SMTP port | Use port 587 with STARTTLS (not 465 with SSL) |
| Bot replies repeatedly | Email not marked as read | Always call `mark_as_read()` after processing |

---

## Best Practices

- Store credentials in `.env` — never hardcode them
- Always skip emails where `from` matches your own address
- Use `mark_as_read()` immediately after processing to avoid duplicate replies
- Add logging (`import logging`) in production instead of `print()`
- For high volume, use a database to track processed email IDs
- Add rate limiting — avoid sending more than 500 emails/day on Gmail free accounts

---

## Dependencies

```
python-dotenv
```

Install:
```bash
pip install python-dotenv
```

> `smtplib` and `imaplib` are Python built-ins — no extra install needed.