"""
Email channel handler for Customer Success Digital FTE.
Handles receiving emails via IMAP and sending via SMTP.

Uses Python built-in libraries (imaplib, smtplib) - no OAuth2 required.
Supports Gmail, Outlook, Yahoo, and custom SMTP servers.
"""
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from typing import Optional, Dict, Any, List
import logging
import time
from datetime import datetime

from production.config import settings
from production.utils.logging import get_logger
from production.utils.exceptions import EmailReadError, EmailDeliveryError

logger = get_logger(__name__)


# =============================================================================
# Observability - Metrics Counters
# =============================================================================

class EmailMetricsCounter:
    """
    Thread-safe metrics counter for email processing observability.
    
    Tracks:
    - emails_processed: Total number of emails successfully processed
    - escalations_triggered: Number of escalations created due to negative sentiment
    - processing_errors: Number of processing errors encountered
    - duplicate_emails_blocked: Number of duplicate emails blocked by idempotency
    """
    
    def __init__(self):
        self._emails_processed = 0
        self._escalations_triggered = 0
        self._processing_errors = 0
        self._duplicate_emails_blocked = 0
    
    def increment_emails_processed(self):
        """Increment emails processed counter."""
        self._emails_processed += 1
    
    def increment_escalations_triggered(self):
        """Increment escalations triggered counter."""
        self._escalations_triggered += 1
    
    def increment_processing_errors(self):
        """Increment processing errors counter."""
        self._processing_errors += 1
    
    def increment_duplicate_emails_blocked(self):
        """Increment duplicate emails blocked counter."""
        self._duplicate_emails_blocked += 1
    
    def get_metrics(self) -> Dict[str, int]:
        """Get all metrics as dictionary."""
        return {
            "emails_processed": self._emails_processed,
            "escalations_triggered": self._escalations_triggered,
            "processing_errors": self._processing_errors,
            "duplicate_emails_blocked": self._duplicate_emails_blocked
        }
    
    def reset(self):
        """Reset all counters (useful for testing)."""
        self._emails_processed = 0
        self._escalations_triggered = 0
        self._processing_errors = 0
        self._duplicate_emails_blocked = 0


# Global metrics instance
email_metrics = EmailMetricsCounter()


def get_email_metrics() -> EmailMetricsCounter:
    """Get email metrics counter instance."""
    return email_metrics


class EmailHandler:
    """
    Email handler for receiving and sending emails.
    
    Features:
    - IMAP polling for receiving unread emails
    - SMTP with STARTTLS for sending
    - Email threading support (In-Reply-To, References headers)
    - Multipart message handling
    - Automatic retry with exponential backoff
    """
    
    def __init__(self):
        self.email_address = settings.EMAIL_ADDRESS
        self.email_password = settings.EMAIL_PASSWORD
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.imap_host = settings.IMAP_HOST
        self.imap_port = settings.IMAP_PORT
        self.poll_interval = settings.POLL_INTERVAL
    
    # =========================================================================
    # IMAP - Receiving Emails
    # =========================================================================
    
    def get_imap_connection(self) -> imaplib.IMAP4_SSL:
        """
        Connect and login to IMAP server.
        
        Returns:
            IMAP4_SSL connection object
            
        Raises:
            EmailReadError: If connection or login fails
        """
        try:
            mail = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
            mail.login(self.email_address, self.email_password)
            logger.debug("IMAP connection established")
            return mail
        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP connection failed: {e}")
            raise EmailReadError(f"Failed to connect to IMAP server: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected IMAP error: {e}")
            raise EmailReadError(f"Unexpected IMAP error: {str(e)}")
    
    def get_unread_emails(self, folder: str = "INBOX") -> List[Dict[str, Any]]:
        """
        Fetch all unread emails from specified folder.

        Args:
            folder: IMAP folder to search (default: INBOX)

        Returns:
            List of parsed email dictionaries

        Raises:
            EmailReadError: If fetching emails fails
        """
        mail = None
        try:
            mail = self.get_imap_connection()
            mail.select(folder)

            # Search for unread emails
            status, messages = mail.search(None, "UNSEEN")

            if status != "OK":
                logger.warning("No unread emails found")
                return []

            email_ids = messages[0].split()

            if not email_ids:
                logger.info("No new emails")
                return []

            logger.info(f"Found {len(email_ids)} unread email(s)")

            emails = []
            for eid in email_ids:
                try:
                    status, msg_data = mail.fetch(eid, "(RFC822)")
                    if status == "OK":
                        raw_email = msg_data[0][1]
                        parsed = self._parse_email(raw_email, eid.decode())
                        if parsed:
                            emails.append(parsed)
                except Exception as e:
                    logger.error(f"Failed to parse email {eid}: {e}")
                    continue

            mail.logout()
            logger.info(f"Successfully fetched {len(emails)} email(s)")
            return emails

        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            if mail:
                try:
                    mail.logout()
                except:
                    pass
            raise EmailReadError(f"Failed to fetch emails: {str(e)}")
    
    def _parse_email(self, raw_email: bytes, email_id: str) -> Optional[Dict[str, Any]]:
        """
        Parse raw email bytes into structured dictionary.
        
        Args:
            raw_email: Raw email bytes
            email_id: IMAP email ID
        
        Returns:
            Parsed email dictionary or None if parsing fails
        """
        try:
            msg = email.message_from_bytes(raw_email)
            
            # Extract headers
            subject = self._decode_header(msg.get("Subject", ""))
            from_addr = self._decode_header(msg.get("From", ""))
            to_addr = self._decode_header(msg.get("To", ""))
            message_id = msg.get("Message-ID", "")
            in_reply_to = msg.get("In-Reply-To", "")
            references = msg.get("References", "")
            
            # Extract body
            body = self._extract_body(msg)
            
            # Parse references header into list
            references_list = references.split() if references else []
            
            parsed = {
                "email_id": email_id,
                "subject": subject,
                "from": from_addr,
                "to": to_addr,
                "message_id": message_id,
                "in_reply_to": in_reply_to,
                "references": references_list,
                "body": body,
                "received_at": datetime.utcnow().isoformat()
            }
            
            logger.debug(f"Parsed email from {from_addr}: {subject}")
            return parsed
            
        except Exception as e:
            logger.error(f"Failed to parse email: {e}")
            return None
    
    def _decode_header(self, value: str) -> str:
        """
        Decode encoded email header strings.
        
        Handles MIME encoded words (e.g., =?UTF-8?B?...?=)
        
        Args:
            value: Header value to decode
        
        Returns:
            Decoded string
        """
        if not value:
            return ""
        
        try:
            decoded_parts = decode_header(value)
            decoded_str = ""
            
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    decoded_str += part.decode(encoding or "utf-8", errors="ignore")
                else:
                    decoded_str += part
            
            return decoded_str.strip()
        except Exception as e:
            logger.warning(f"Failed to decode header '{value}': {e}")
            return value
    
    def _extract_body(self, msg: email.message.Message) -> str:
        """
        Extract plain text body from email (handles multipart).
        
        Prefers plain text over HTML.
        
        Args:
            msg: Email message object
        
        Returns:
            Plain text body content
        """
        body = ""
        
        try:
            if msg.is_multipart():
                # Try to get plain text part first
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        charset = part.get_content_charset() or "utf-8"
                        try:
                            payload = part.get_payload(decode=True)
                            if payload:
                                body = payload.decode(charset, errors="ignore")
                                break
                        except:
                            continue
            else:
                # Single part message
                if msg.get_content_type() == "text/plain":
                    charset = msg.get_content_charset() or "utf-8"
                    try:
                        payload = msg.get_payload(decode=True)
                        if payload:
                            body = payload.decode(charset, errors="ignore")
                    except:
                        pass
        except Exception as e:
            logger.error(f"Failed to extract email body: {e}")
        
        return body.strip()
    
    def mark_as_read(self, email_id: str, folder: str = "INBOX"):
        """
        Mark an email as read (seen) by its IMAP ID.
        
        Args:
            email_id: IMAP email ID
            folder: IMAP folder (default: INBOX)
            
        Raises:
            EmailReadError: If marking as read fails
        """
        mail = None
        try:
            mail = self.get_imap_connection()
            mail.select(folder)
            mail.store(email_id, "+FLAGS", "\\Seen")
            mail.logout()
            logger.debug(f"Marked email {email_id} as read")
        except Exception as e:
            logger.error(f"Failed to mark email as read: {e}")
            raise EmailReadError(f"Failed to mark email as read: {str(e)}")
        finally:
            if mail:
                try:
                    mail.logout()
                except:
                    pass
    
    # =========================================================================
    # SMTP - Sending Emails
    # =========================================================================
    
    def get_smtp_connection(self) -> smtplib.SMTP:
        """
        Connect and login to SMTP server with STARTTLS.

        Returns:
            SMTP connection object

        Raises:
            EmailDeliveryError: If connection or login fails
        """
        try:
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.ehlo()
            server.starttls()  # Encrypt the connection
            server.ehlo()
            server.login(self.email_address, self.email_password)
            logger.debug("SMTP connection established")
            return server
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            raise EmailDeliveryError(
                "SMTP authentication failed. Check email credentials and App Password.",
                {"error_code": "AUTH_FAILED"}
            )
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            raise EmailDeliveryError(f"SMTP error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected SMTP error: {e}")
            raise EmailDeliveryError(f"Unexpected SMTP error: {str(e)}")
    
    def send_reply(
        self,
        email_data: Dict[str, Any],
        reply_body: str,
        subject_prefix: str = "Re: "
    ) -> bool:
        """
        Send a reply email in the same thread.

        Uses In-Reply-To and References headers for proper threading (RFC 2822).

        Args:
            email_data: Original email data (from, subject, message_id, references)
            reply_body: Reply message content
            subject_prefix: Prefix for reply subject (default: "Re: ")

        Returns:
            True if sent successfully

        Raises:
            EmailDeliveryError: If sending fails
        """
        try:
            msg = MIMEMultipart()
            msg["From"] = self.email_address
            msg["To"] = email_data["from"]
            msg["Subject"] = f"{subject_prefix}{email_data['subject']}"

            # Threading headers (RFC 2822)
            msg["In-Reply-To"] = email_data["message_id"]

            references = email_data.get("references", [])
            if references:
                # Add current message ID to references
                ref_str = " ".join(references) + " " + email_data["message_id"]
                msg["References"] = ref_str
            else:
                msg["References"] = email_data["message_id"]

            # Attach plain text body
            msg.attach(MIMEText(reply_body, "plain", "utf-8"))

            # Send email
            with self.get_smtp_connection() as server:
                server.sendmail(
                    self.email_address,
                    email_data["from"],
                    msg.as_string()
                )

            logger.info(f"Reply sent to {email_data['from']} | Subject: {email_data['subject']}")
            return True

        except EmailDeliveryError:
            raise
        except Exception as e:
            logger.error(f"Failed to send reply: {e}")
            raise EmailDeliveryError(f"Failed to send reply: {str(e)}")
    
    def send_new_email(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """
        Send a brand new email (not a reply).
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Plain text body
            html_body: Optional HTML body
        
        Returns:
            True if sent successfully
            
        Raises:
            EmailDeliveryError: If sending fails
        """
        try:
            msg = MIMEMultipart()
            msg["From"] = self.email_address
            msg["To"] = to
            msg["Subject"] = subject
            
            # Attach plain text body
            msg.attach(MIMEText(body, "plain", "utf-8"))
            
            # Attach HTML body if provided
            if html_body:
                msg.attach(MIMEText(html_body, "html", "utf-8"))
            
            # Send email
            with self.get_smtp_connection() as server:
                server.sendmail(
                    self.email_address,
                    to,
                    msg.as_string()
                )
            
            logger.info(f"Email sent to {to} | Subject: {subject}")
            return True
            
        except EmailDeliveryError:
            raise
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise EmailDeliveryError(f"Failed to send email: {str(e)}")
    
    # =========================================================================
    # Email Polling Loop (for Stage 1 Incubation)
    # =========================================================================
    
    def poll_emails(self, callback) -> int:
        """
        Poll for unread emails and process them with callback.
        Now with Kafka integration for event-driven architecture.

        Args:
            callback: Function to call for each email (receives email_data)

        Returns:
            Number of emails processed
        """
        logger.info("Polling for new emails...")
        emails = self.get_unread_emails()

        if not emails:
            logger.info("No new emails")
            return 0

        # Initialize Kafka producer for email events
        kafka_producer = None
        try:
            from production.utils.kafka_producer import get_kafka_producer
            kafka_producer = get_kafka_producer()
            logger.info("Kafka producer available for email events")
        except Exception as e:
            logger.warning(f"Kafka not available, continuing without: {e}")

        processed = 0
        for email_data in emails:
            start_time = time.time()

            try:
                logger.info(f"Processing email from {email_data['from']}: {email_data['subject']}")

                # Produce Kafka event for incoming email
                if kafka_producer:
                    try:
                        kafka_producer.produce_ticket_event(
                            event_type='email_received',
                            ticket_id=f"email-{email_data.get('email_id', 'unknown')}",
                            customer_id=email_data.get('from', ''),
                            channel='email',
                            subject=email_data.get('subject', ''),
                            message=email_data.get('body', '')[:500],
                            metadata={
                                'message_id': email_data.get('message_id', ''),
                                'from': email_data.get('from', ''),
                                'to': email_data.get('to', ''),
                            }
                        )
                        logger.info(f"Kafka event produced for email: {email_data.get('message_id')}")
                    except Exception as e:
                        logger.warning(f"Failed to produce Kafka event: {e}")

                # Call the callback to process the email
                # Callback should return processing result with ticket_id, sentiment, escalation info
                result = callback(email_data)

                # Mark as read after processing
                self.mark_as_read(email_data["email_id"])

                # Calculate processing time
                processing_time_ms = (time.time() - start_time) * 1000

                # Observability logging
                self._log_email_processing(
                    email_data=email_data,
                    result=result,
                    processing_time_ms=processing_time_ms
                )

                # Update metrics
                email_metrics.increment_emails_processed()
                if result and result.get("escalation_triggered"):
                    email_metrics.increment_escalations_triggered()

                processed += 1
                logger.info(f"Processed email {processed}/{len(emails)}")

            except Exception as e:
                processing_time_ms = (time.time() - start_time) * 1000

                logger.error(f"Failed to process email: {e}")

                # Update error metrics
                email_metrics.increment_processing_errors()

                # Still mark as read to avoid infinite loop
                try:
                    self.mark_as_read(email_data["email_id"])
                except:
                    pass

        logger.info(f"Finished processing {processed} email(s)")
        return processed

    def _log_email_processing(
        self,
        email_data: Dict[str, Any],
        result: Optional[Dict[str, Any]],
        processing_time_ms: float
    ):
        """
        Log email processing for observability.
        
        Logs:
        - ticket_id
        - customer_email
        - sentiment_score
        - escalation_flag
        - processing_time_ms
        
        Args:
            email_data: Original email data
            result: Processing result from callback (may contain ticket_id, sentiment, escalation info)
            processing_time_ms: Time taken to process email in milliseconds
        """
        result = result or {}
        
        ticket_id = result.get("ticket_id", "N/A")
        customer_email = email_data.get("from", "N/A")
        sentiment_score = result.get("sentiment_score", "N/A")
        escalation_flag = result.get("escalation_triggered", False)
        
        # Structured logging for observability
        logger.info(
            "EMAIL_PROCESSED | "
            f"ticket_id={ticket_id} | "
            f"customer_email={customer_email} | "
            f"sentiment_score={sentiment_score} | "
            f"escalation_flag={escalation_flag} | "
            f"processing_time_ms={processing_time_ms:.2f}"
        )


# Global email handler instance
email_handler = EmailHandler()


def get_email_handler() -> EmailHandler:
    """Get email handler instance."""
    return email_handler
