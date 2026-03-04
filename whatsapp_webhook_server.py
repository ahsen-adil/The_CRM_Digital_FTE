"""
WhatsApp Webhook Endpoint (FastAPI)

Receives incoming WhatsApp messages from Whapi.Cloud and processes them with AI.

Usage:
    uvicorn whatsapp_webhook_server:app --reload --host 0.0.0.0 --port 8000
    
Configure webhook in Whapi dashboard:
    Settings → Webhooks → https://your-server.com:8000/whatsapp-webhook
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import asyncio
import time
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from concurrent.futures import ThreadPoolExecutor
from production.config import settings
from production.agent.customer_success_agent import run_agent_sync
from src.channels.whatsapp_handler import WhatsAppHandler

app = FastAPI(title="WhatsApp Webhook", version="1.0.0")

# Thread pool for async processing
executor = ThreadPoolExecutor(max_workers=10)

# Store processed message IDs to prevent duplicates
processed_messages = set()
MAX_STORED_IDS = 10000


def run_ai_agent_sync(customer_email, subject, message_body):
    """Run AI agent in separate thread to avoid event loop conflicts"""
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as exec:
        future = exec.submit(run_agent_sync, customer_email, subject, message_body)
        return future.result()


def get_db_conn():
    """Get database connection"""
    return psycopg2.connect(settings.DATABASE_URL, sslmode='require')


def create_customer_whatsapp(phone_number, name=None):
    """Create/find customer by WhatsApp number"""
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if exists by phone_number
            cur.execute("SELECT * FROM customers WHERE phone_number = %s", (phone_number,))
            existing = cur.fetchone()
            
            if existing:
                return dict(existing), False  # existing, not new
            
            # Create new - use phone_number as email placeholder
            email_placeholder = f"{phone_number}@whatsapp.com"
            cur.execute(
                "INSERT INTO customers (phone_number, name, email) VALUES (%s, %s, %s) RETURNING *",
                (phone_number, name, email_placeholder)
            )
            customer = cur.fetchone()
            conn.commit()
            return dict(customer), True  # new customer
    finally:
        conn.close()


def create_conversation(customer_id, topic):
    """Create conversation"""
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO conversations (customer_id, topic, status) VALUES (%s, %s, 'open') RETURNING *",
                (customer_id, topic)
            )
            conversation = cur.fetchone()
            conn.commit()
            return dict(conversation)
    finally:
        conn.close()


def create_ticket(customer_id, channel, description, conversation_id):
    """Create ticket"""
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO tickets (customer_id, channel, description, conversation_id, status)
                VALUES (%s, %s, %s, %s, 'open') RETURNING *
                """,
                (customer_id, channel, description, conversation_id)
            )
            ticket = cur.fetchone()
            conn.commit()
            return dict(ticket)
    finally:
        conn.close()


def log_ai_interaction(ticket_id, customer_email, original_message, ai_response,
                       sentiment_score, confidence_score, escalation_flag,
                       escalation_reason, category, priority, processing_time_ms):
    """Log AI interaction"""
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO ai_interactions (
                    ticket_id, customer_email, original_message, ai_response,
                    sentiment_score, confidence_score, escalation_flag, escalation_reason,
                    category, priority, processing_time_ms
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (ticket_id, customer_email, original_message, ai_response,
                 sentiment_score, confidence_score, escalation_flag, escalation_reason,
                 category, priority, processing_time_ms)
            )
            conn.commit()
    finally:
        conn.close()


def process_message_sync(message_data):
    """
    Process WhatsApp message synchronously in thread pool.
    
    Flow:
    1. Create/Find customer
    2. Create conversation
    3. Create ticket
    4. Call AI agent
    5. Log AI interaction
    6. Check escalation
    7. Send WhatsApp reply
    """
    message_id = message_data['id']
    phone_number = message_data['from'].split('@')[0]
    customer_name = message_data.get('from_name', 'WhatsApp User')
    message_body = message_data['text']['body']
    
    start_time = time.time()
    
    print(f"\n{'='*80}")
    print(f"[WHATSAPP] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    print(f"From: {customer_name} ({phone_number})")
    print(f"Message ID: {message_id}")
    print(f"Message: {message_body[:200]}")
    print(f"{'='*80}\n")
    
    try:
        # STEP 1: Customer
        print("[STEP 1/7] Creating customer...")
        customer, is_new = create_customer_whatsapp(phone_number, customer_name)
        customer_id = customer['id']
        print(f"  [{'OK' if not is_new else 'NEW'}] Customer: {customer_id}")
        
        # STEP 2: Conversation
        print("[STEP 2/7] Creating conversation...")
        conversation = create_conversation(customer_id, "WhatsApp Support")
        conversation_id = conversation['id']
        print(f"  [OK] Conversation: {conversation_id}")
        
        # STEP 3: Ticket
        print("[STEP 3/7] Creating ticket...")
        ticket = create_ticket(
            customer_id=customer_id,
            channel='whatsapp',
            description=message_body,
            conversation_id=conversation_id
        )
        ticket_id = ticket['id']
        ticket_number = ticket['ticket_number']
        print(f"  [OK] Ticket: {ticket_number}")
        
        # STEP 4: AI Agent
        print("[STEP 4/7] Calling AI agent...")
        ai_start = time.time()
        ai_response = run_ai_agent_sync(
            f"{phone_number}@whatsapp.com",
            "WhatsApp Support",
            message_body
        )
        ai_time = int((time.time() - ai_start) * 1000)
        print(f"  [OK] AI: {ai_time}ms | Sentiment: {ai_response.sentiment_score} | Escalation: {ai_response.escalation_required}")
        
        # STEP 5: Log AI
        print("[STEP 5/7] Logging AI interaction...")
        log_ai_interaction(
            ticket_id=ticket_id,
            customer_email=f"{phone_number}@whatsapp.com",
            original_message=message_body,
            ai_response=ai_response.reply_text,
            sentiment_score=ai_response.sentiment_score,
            confidence_score=ai_response.confidence_score,
            escalation_flag=ai_response.escalation_required,
            escalation_reason=ai_response.escalation_reason,
            category=ai_response.category,
            priority=ai_response.priority,
            processing_time_ms=ai_time
        )
        print(f"  [OK] Logged")
        
        # STEP 6: Escalation
        print("[STEP 6/7] Checking escalation...")
        if ai_response.escalation_required:
            print(f"  [WARN] Escalation: {ai_response.escalation_reason}")
        else:
            print(f"  [OK] No escalation")
        
        # STEP 7: Send Reply
        print("[STEP 7/7] Sending WhatsApp reply...")
        handler = WhatsAppHandler()
        
        # Format for WhatsApp (shorter, conversational)
        reply_text = ai_response.reply_text[:500] if len(ai_response.reply_text) > 500 else ai_response.reply_text
        
        success = handler.send_reply(message_data, reply_text)
        print(f"  [OK] Reply sent: {success}")
        
        total_time = int((time.time() - start_time) * 1000)
        
        print(f"\n{'='*80}")
        print(f"[COMPLETE] Ticket: {ticket_number} | Time: {total_time}ms")
        print(f"{'='*80}\n")
        
        # Mark as processed
        processed_messages.add(message_id)
        
        # Cleanup old IDs
        if len(processed_messages) > MAX_STORED_IDS:
            # Remove oldest 10%
            to_remove = list(processed_messages)[:MAX_STORED_IDS // 10]
            for id in to_remove:
                processed_messages.discard(id)
        
        return {
            "success": True,
            "ticket_id": ticket_id,
            "ticket_number": ticket_number,
            "processing_time_ms": total_time
        }
        
    except Exception as e:
        print(f"\n{'='*80}")
        print(f"[ERROR] {type(e).__name__}: {e}")
        print(f"{'='*80}")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/whatsapp-webhook")
async def whatsapp_webhook(request: Request):
    """
    Receive WhatsApp messages from Whapi.Cloud
    
    LOGGING: This endpoint logs EVERY request for debugging
    """
    print(f"\n{'='*80}")
    print(f"[WEBHOOK RECEIVED] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    
    try:
        # Log raw request
        body = await request.json()
        print(f"[WEBHOOK] Raw payload:")
        print(f"  Keys: {list(body.keys())}")
        print(f"  Messages count: {len(body.get('messages', []))}")
        print(f"  Full payload: {body}")
        
        messages = body.get('messages', [])
        
        if not messages:
            print(f"[WEBHOOK] No messages in payload")
            return JSONResponse(
                content={"status": "ok", "message": "No messages to process"},
                status_code=200
            )
        
        processed_count = 0
        results = []
        
        for msg in messages:
            print(f"\n[MESSAGE] Processing message:")
            print(f"  ID: {msg.get('id')}")
            print(f"  From: {msg.get('from')}")
            print(f"  From Name: {msg.get('from_name')}")
            print(f"  Type: {msg.get('type')}")
            print(f"  From Me: {msg.get('from_me')}")
            print(f"  Text: {msg.get('text', {}).get('body', '')[:100]}")
            
            # Skip if from ourselves
            if msg.get('from_me', True):
                print(f"  [SKIP] Message from ourselves")
                continue
            
            # Skip if not text
            if msg.get('type') != 'text':
                print(f"  [SKIP] Not a text message")
                continue
            
            # Skip if already processed (idempotency)
            message_id = msg.get('id', '')
            if message_id in processed_messages:
                print(f"  [SKIP] Already processed")
                continue
            
            print(f"  [OK] Processing message...")
            
            # Process in thread pool (non-blocking)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                executor,
                process_message_sync,
                msg
            )
            
            results.append(result)
            processed_count += 1
        
        print(f"\n[WEBHOOK] Processed {processed_count} message(s)")
        print(f"{'='*80}\n")
        
        success_count = sum(1 for r in results if r.get('success', False))
        
        return JSONResponse(
            content={
                "status": "ok",
                "processed": processed_count,
                "successful": success_count,
                "failed": processed_count - success_count
            },
            status_code=200
        )
        
    except Exception as e:
        print(f"\n{'='*80}")
        print(f"[WEBHOOK ERROR] {type(e).__name__}: {e}")
        print(f"{'='*80}")
        import traceback
        traceback.print_exc()
        
        return JSONResponse(
            content={
                "status": "error",
                "message": str(e),
                "type": type(e).__name__
            },
            status_code=500
        )


@app.post("/messages")
async def messages_webhook(request: Request):
    """
    Compatibility endpoint for Whapi.Cloud default webhook URL.
    Forwards to /whatsapp-webhook handler.
    """
    print(f"\n{'='*80}")
    print(f"[WHAPI MESSAGE] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    print(f"[INFO] Received on /messages endpoint - forwarding to /whatsapp-webhook")
    
    # Call the main webhook handler
    return await whatsapp_webhook(request)


@app.post("/whatsapp-webhook/messages")
async def whatsapp_webhook_messages(request: Request):
    """
    Compatibility endpoint for Whapi.Cloud when configured with /whatsapp-webhook/messages.
    Forwards to /whatsapp-webhook handler.
    """
    print(f"\n{'='*80}")
    print(f"[WHAPI MESSAGE] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    print(f"[INFO] Received on /whatsapp-webhook/messages endpoint - forwarding to handler")
    
    # Call the main webhook handler
    return await whatsapp_webhook(request)


@app.post("/whatsapp-webhook-sync")
async def whatsapp_webhook_sync(request: Request):
    """
    Synchronous webhook endpoint (for testing).
    Processes messages immediately and waits for completion.
    """
    return await whatsapp_webhook(request)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "processed_messages": len(processed_messages)
    }


@app.get("/stats")
async def stats():
    """Show processing statistics"""
    return {
        "processed_messages_count": len(processed_messages),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/")
async def root():
    """Root endpoint with API info and test instructions"""
    print(f"[API] Root endpoint accessed")
    return {
        "service": "WhatsApp Webhook",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "webhook": "POST /whatsapp-webhook",
            "webhook_sync": "POST /whatsapp-webhook-sync",
            "test": "POST /test-webhook (send test message)",
            "health": "GET /health",
            "stats": "GET /stats"
        },
        "instructions": {
            "test": "POST to /test-webhook with {'message': 'hello'}",
            "whapi_webhook": "Configure in Whapi dashboard: Settings → Webhooks → http://your-server:8000/whatsapp-webhook"
        }
    }


@app.post("/test-webhook")
async def test_webhook(request: Request):
    """
    Test endpoint - simulates incoming WhatsApp message
    
    Usage:
    curl -X POST http://localhost:8000/test-webhook \\
      -H "Content-Type: application/json" \\
      -d '{"from": "923001234567", "from_name": "Test User", "message": "Hello"}'
    """
    print(f"\n{'='*80}")
    print(f"[TEST WEBHOOK] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    
    try:
        data = await request.json()
        from_number = data.get('from', '923001234567')
        from_name = data.get('from_name', 'Test User')
        message = data.get('message', 'Hello from test')
        
        print(f"[TEST] Simulating WhatsApp message:")
        print(f"  From: {from_name} ({from_number})")
        print(f"  Message: {message}")
        
        # Create simulated message in Whapi format
        test_message = {
            "id": f"test-{int(time.time())}",
            "from_me": False,
            "type": "text",
            "chat_id": f"{from_number}@c.us",
            "timestamp": int(time.time()),
            "text": {"body": message},
            "from": from_number,
            "from_name": from_name
        }
        
        print(f"[TEST] Processing message...")
        
        # Process the test message
        result = process_message_sync(test_message)
        
        print(f"\n{'='*80}")
        print(f"[TEST COMPLETE]")
        print(f"{'='*80}\n")
        
        return {
            "status": "ok",
            "message": "Test message processed",
            "result": result
        }
        
    except Exception as e:
        print(f"[TEST ERROR] {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*80)
    print("WHATSAPP WEBHOOK SERVER (FastAPI)")
    print("="*80)
    print(f"\n🚀 Starting server...")
    print(f"📡 Webhook URL: http://localhost:8000/whatsapp-webhook")
    print(f"\n🔧 Configuration:")
    print(f"  WHAPI_API_KEY: {'✅ Set' if settings.WHAPI_API_KEY else '❌ Not set'}")
    print(f"  WHAPI_PHONE_ID: {'✅ Set' if settings.WHAPI_PHONE_ID else '❌ Not set'}")
    print(f"  DATABASE_URL: {'✅ Set' if settings.DATABASE_URL else '❌ Not set'}")
    print(f"\n📝 Configure webhook in Whapi dashboard:")
    print(f"   1. Go to: https://panel.whapi.cloud")
    print(f"   2. Settings → Webhooks")
    print(f"   3. Add webhook URL: http://your-server:8000/whatsapp-webhook")
    print(f"   4. Select events: messages.post")
    print(f"\n🧪 Test the webhook:")
    print(f"   curl -X POST http://localhost:8000/test-webhook \\")
    print(f"     -H 'Content-Type: application/json' \\")
    print(f"     -d '{{\"from\": \"923001234567\", \"from_name\": \"Test\", \"message\": \"hello\"}}'")
    print(f"\n💡 Endpoints:")
    print(f"   POST /whatsapp-webhook    - Receive WhatsApp messages")
    print(f"   POST /test-webhook        - Test webhook (simulated message)")
    print(f"   GET  /health              - Health check")
    print(f"   GET  /stats               - Processing statistics")
    print(f"   GET  /                    - API info")
    print(f"\n{'='*80}")
    print(f"\n⏳  Press Ctrl+C to stop\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
