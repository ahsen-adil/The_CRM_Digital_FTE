---
name: whapi-integration
description: Use this skill whenever the user wants to integrate WhatsApp messaging into their application using Whapi.Cloud. Trigger this skill when the user mentions sending WhatsApp messages, receiving WhatsApp messages, setting up webhooks for WhatsApp, managing WhatsApp groups, or building any WhatsApp automation or bot. Also trigger when the user mentions Whapi, WhatsApp API, or wants to programmatically send notifications, alerts, or messages via WhatsApp.
---

# Whapi.Cloud WhatsApp Integration SKILL

## Overview
Whapi.Cloud is a WhatsApp API gateway that allows you to send/receive messages, manage groups, and handle webhooks via HTTP requests.

## Setup (First Time)

1. Create an account: https://whapi.cloud
2. Open a Channel in the Dashboard
3. Scan the QR code in WhatsApp (Linked Devices)
4. Copy the API Token from the dashboard

**Base URL:** `https://gate.whapi.cloud`  
**Auth:** Bearer Token (in header: `Authorization: Bearer YOUR_TOKEN`)

---

## 1. Send a Text Message

### Endpoint
```
POST https://gate.whapi.cloud/messages/text
```

### Headers
```json
{
  "Authorization": "Bearer YOUR_TOKEN",
  "Content-Type": "application/json"
}
```

### Body
```json
{
  "to": "923001234567",
  "body": "Hello! This message is from Whapi."
}
```

> **Note:** Number must be in international format **without** the `+` sign. For Pakistan, start with `92`.

### Python Example
```python
import requests

token = "YOUR_TOKEN"
url = "https://gate.whapi.cloud/messages/text"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

payload = {
    "to": "923001234567",
    "body": "Hello World from Whapi!"
}

response = requests.post(url, json=payload, headers=headers)
print(response.json())
```


---

## 2. Send Media Message (Image/Video/Document)

### Endpoint
```
POST https://gate.whapi.cloud/messages/image
POST https://gate.whapi.cloud/messages/video
POST https://gate.whapi.cloud/messages/document
POST https://gate.whapi.cloud/messages/audio
```

### Body (via URL)
```json
{
  "to": "923001234567",
  "media": "https://example.com/image.jpg",
  "caption": "This is a test image"
}
```

### Body (via Base64)
```json
{
  "to": "923001234567",
  "media": "data:image/jpeg;base64,/9j/4AAQ...",
  "caption": "Base64 image"
}
```

---

## 3. Message with Buttons

### Endpoint
```
POST https://gate.whapi.cloud/messages/interactive/buttons
```

### Body
```json
{
  "to": "923001234567",
  "header": {
    "type": "text",
    "text": "Your order is ready!"
  },
  "body": {
    "text": "Would you like to confirm?"
  },
  "action": {
    "buttons": [
      { "id": "btn_yes", "title": "Yes, confirm" },
      { "id": "btn_no", "title": "No" }
    ]
  }
}
```

---

## 4. Group Message

### Endpoint
```
POST https://gate.whapi.cloud/messages/text
```

### Body (use Group ID)
```json
{
  "to": "120363XXXXXXXXXX@g.us",
  "body": "Hello everyone in the group!"
}
```

### Get Group List
```
GET https://gate.whapi.cloud/groups
```

### Create a Group
```
POST https://gate.whapi.cloud/groups

Body:
{
  "subject": "Test Group",
  "participants": ["923001234567", "923009876543"]
}
```

---

## 5. Webhook Setup (Receive Messages)

### Set Webhook URL (via API)
```
PUT https://gate.whapi.cloud/settings
```

```json
{
  "webhooks": [
    {
      "url": "https://yourserver.com/webhook",
      "events": [
        { "type": "messages", "method": "post" },
        { "type": "statuses", "method": "put" }
      ]
    }
  ]
}
```

### Incoming Message Format
```json
{
  "messages": [
    {
      "id": "msg_id_here",
      "from_me": false,
      "type": "text",
      "chat_id": "[email protected]",
      "timestamp": 1712995245,
      "text": { "body": "User's message" },
      "from": "923001234567",
      "from_name": "User Name"
    }
  ],
  "event": { "type": "messages", "event": "post" },
  "channel_id": "YOUR_CHANNEL_ID"
}
```

### Webhook Server (Python/FastAPI)
```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI()

@app.post('/webhook')
async def webhook(request: Request):
    data = await request.json()
    messages = data.get('messages', [])

    for msg in messages:
        if not msg.get('from_me') and msg.get('type') == 'text':
            sender = msg.get('from_name')
            text = msg['text']['body']
            print(f"Message from {sender}: {text}")
            # Auto-reply logic here

    return JSONResponse(content={"status": "ok"}, status_code=200)

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=3000)
```

> Install dependencies: `pip install fastapi uvicorn`

---

## 6. Check if Number is on WhatsApp

### Endpoint
```
POST https://gate.whapi.cloud/contacts/check
```

### Body
```json
{
  "contacts": ["923001234567", "923009876543"]
}
```

---

## 7. Track Message Status

Message status comes via the `statuses.post` webhook event:

| Status | Meaning |
|--------|---------|
| `pending` | Being sent |
| `sent` | Delivered to WhatsApp server |
| `delivered` | Reached recipient (2 checkmarks) |
| `read` | Read by recipient (2 blue checkmarks) |
| `failed` | Could not be sent |

---

## Common Mistakes & Solutions

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Wrong token | Check token from dashboard |
| `pending` status | Normal, not the final status | Track status via webhook |
| Number not added to group | Number not registered on WhatsApp | Use `/contacts/check` first |
| Webhook not receiving | URL not publicly accessible | Use ngrok or a real server |

---

## Rate Limiting & Best Practices

- Add a delay between messages (minimum 1-2 seconds)
- Use batching for bulk messages
- Avoid spam-like patterns (account can get banned)
- Apply `from_me = false` filter to only process incoming messages
- Webhook response must always be 200 OK, otherwise retries will occur

---

## Useful Links

- API Docs: https://whapi.readme.io
- Dashboard: https://panel.whapi.cloud
- Help Desk: https://support.whapi.cloud
- GitHub Examples: https://github.com/Whapi-Cloud