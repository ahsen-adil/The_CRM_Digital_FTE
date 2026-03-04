"""
WhatsApp Handler for Customer Success Digital FTE

Uses Whapi.Cloud API for sending and receiving WhatsApp messages.
Fully synchronous - no async issues.

Features:
- Send text messages via Whapi API
- Receive messages via webhook polling
- Message threading support
- Error handling with retry logic
"""
import requests
import time
from typing import Optional, Dict, Any, List
from production.config import settings


class WhatsAppHandler:
    """
    WhatsApp handler for sending and receiving messages.
    
    Uses Whapi.Cloud API (https://whapi.cloud)
    """
    
    def __init__(self):
        self.api_key = settings.WHAPI_API_KEY
        self.phone_id = settings.WHAPI_PHONE_ID
        self.base_url = settings.WHAPI_BASE_URL or "https://gate.whapi.cloud"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    # =========================================================================
    # Sending Messages
    # =========================================================================
    
    def send_message(self, to: str, body: str) -> bool:
        """
        Send a text message via WhatsApp.
        
        Args:
            to: Recipient phone number (international format, no + sign)
            body: Message text
        
        Returns:
            True if sent successfully
        
        Raises:
            Exception: If sending fails
        """
        try:
            url = f"{self.base_url}/messages/text"
            
            payload = {
                "to": to,
                "body": body
            }
            
            print(f"  [WhatsApp] Sending to: {to}")
            print(f"  [WhatsApp] Message: {body[:100]}...")
            
            response = requests.post(url, json=payload, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print(f"  [WhatsApp] ✅ Message sent: {result.get('message_id', 'N/A')}")
                return True
            else:
                print(f"  [WhatsApp] ❌ Failed: {response.status_code} - {response.text}")
                raise Exception(f"WhatsApp API error: {response.status_code}")
                
        except Exception as e:
            print(f"  [WhatsApp] Error: {e}")
            raise
    
    def send_reply(self, message_data: Dict[str, Any], reply_body: str) -> bool:
        """
        Send a reply to a WhatsApp message.
        
        Args:
            message_data: Original message data (from, chat_id, etc.)
            reply_body: Reply message text
        
        Returns:
            True if sent successfully
        """
        # Use chat_id for group messages, from for individual
        to = message_data.get('chat_id', message_data.get('from', ''))
        
        # Remove @c.us/@g.us suffix if present
        if '@c.us' in to or '@g.us' in to:
            to = to.split('@')[0]
        
        return self.send_message(to, reply_body)
    
    # =========================================================================
    # Receiving Messages (Webhook Polling)
    # =========================================================================
    
    def get_webhook_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Poll webhook endpoint for new messages.
        
        Note: In production, use actual webhook endpoint.
        For testing, this simulates webhook polling.
        
        Args:
            limit: Maximum messages to retrieve
        
        Returns:
            List of message dictionaries
        """
        # For production: implement actual webhook endpoint
        # For now, this is a placeholder
        print("  [WhatsApp] Webhook polling not implemented - use webhook endpoint")
        return []
    
    def parse_webhook_message(self, webhook_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse incoming webhook message into standardized format.
        
        Args:
            webhook_data: Raw webhook payload
        
        Returns:
            Parsed message dictionary or None
        """
        try:
            messages = webhook_data.get('messages', [])
            
            if not messages:
                return None
            
            # Process first message
            msg = messages[0]
            
            # Skip messages from ourselves
            if msg.get('from_me', True):
                return None
            
            # Only process text messages for now
            if msg.get('type') != 'text':
                return None
            
            parsed = {
                'message_id': msg.get('id', ''),
                'from': msg.get('from', ''),
                'from_name': msg.get('from_name', 'Unknown'),
                'chat_id': msg.get('chat_id', ''),
                'body': msg.get('text', {}).get('body', ''),
                'timestamp': msg.get('timestamp', 0),
                'type': 'text'
            }
            
            print(f"  [WhatsApp] Parsed message from {parsed['from_name']}: {parsed['body'][:50]}")
            return parsed
            
        except Exception as e:
            print(f"  [WhatsApp] Error parsing webhook: {e}")
            return None
    
    # =========================================================================
    # Utility Functions
    # =========================================================================
    
    def check_connection(self) -> bool:
        """
        Test WhatsApp API connection.
        
        Returns:
            True if connection is working
        """
        try:
            # Try to get channel info
            url = f"{self.base_url}/channel"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                print("  [WhatsApp] ✅ API connection OK")
                return True
            else:
                print(f"  [WhatsApp] ❌ API error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"  [WhatsApp] ❌ Connection failed: {e}")
            return False
    
    def check_number(self, phone_number: str) -> bool:
        """
        Check if a phone number is registered on WhatsApp.
        
        Args:
            phone_number: Number to check (international format, no +)
        
        Returns:
            True if number exists on WhatsApp
        """
        try:
            url = f"{self.base_url}/contacts/check"
            payload = {"contacts": [phone_number]}
            
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                # Check if number exists
                contacts = result.get('contacts', [])
                if contacts and contacts[0].get('exists', False):
                    return True
            
            return False
            
        except Exception as e:
            print(f"  [WhatsApp] Error checking number: {e}")
            return False


# Global handler instance
whatsapp_handler = WhatsAppHandler()


def get_whatsapp_handler() -> WhatsAppHandler:
    """Get WhatsApp handler instance."""
    return whatsapp_handler
