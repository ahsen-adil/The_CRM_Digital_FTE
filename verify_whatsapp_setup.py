"""
WhatsApp Webhook Configuration Verifier

Checks if everything is configured correctly for receiving WhatsApp webhooks.
"""
import sys
import os
import requests

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from production.config import settings

print("="*80)
print("WHATSAPP WEBHOOK CONFIGURATION VERIFIER")
print("="*80)

# Check 1: Environment variables
print("\n[CHECK 1] Environment Variables...")
checks_passed = 0
checks_total = 0

checks_total += 1
if settings.WHAPI_API_KEY and settings.WHAPI_API_KEY != "your_whapi_api_key_here":
    print(f"  [OK] WHAPI_API_KEY is set")
    checks_passed += 1
else:
    print(f"  [FAIL] WHAPI_API_KEY is NOT set or still default value")
    print(f"     Add to .env: WHAPI_API_KEY=your_actual_api_key")

checks_total += 1
if settings.WHAPI_PHONE_ID and settings.WHAPI_PHONE_ID != "your_whapi_phone_id_here":
    print(f"  [OK] WHAPI_PHONE_ID is set")
    checks_passed += 1
else:
    print(f"  [FAIL] WHAPI_PHONE_ID is NOT set or still default value")
    print(f"     Add to .env: WHAPI_PHONE_ID=your_phone_id")

checks_total += 1
if settings.DATABASE_URL and settings.DATABASE_URL != "postgresql://...":
    print(f"  [OK] DATABASE_URL is set")
    checks_passed += 1
else:
    print(f"  [FAIL] DATABASE_URL is NOT set or still default value")

checks_total += 1
if settings.WHAPI_BASE_URL:
    print(f"  [OK] WHAPI_BASE_URL is set: {settings.WHAPI_BASE_URL}")
    checks_passed += 1
else:
    print(f"  [WARN] WHAPI_BASE_URL not set (using default)")

# Check 2: Test local server
print(f"\n[CHECK 2] Testing Local Server...")
try:
    response = requests.get("http://localhost:8000/health", timeout=5)
    if response.status_code == 200:
        print(f"  [OK] Server is running on http://localhost:8000")
        print(f"     Health: {response.json().get('status', 'unknown')}")
        checks_passed += 1
    else:
        print(f"  [FAIL] Server returned status {response.status_code}")
except requests.exceptions.ConnectionError:
    print(f"  [FAIL] Server is NOT running on http://localhost:8000")
    print(f"     Start with: uvicorn whatsapp_webhook_server:app --reload")
except Exception as e:
    print(f"  [FAIL] Error testing server: {e}")

checks_total += 1

# Check 3: Test for ngrok
print(f"\n[CHECK 3] Checking for ngrok...")
try:
    response = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=5)
    if response.status_code == 200:
        tunnels = response.json().get('tunnels', [])
        public_tunnel = None
        for tunnel in tunnels:
            if tunnel.get('proto', '').upper() == 'HTTPS':
                public_tunnel = tunnel.get('public_url', '')
                break
        
        if public_tunnel:
            print(f"  [OK] ngrok is running")
            print(f"     Public URL: {public_tunnel}")
            print(f"     Webhook URL: {public_tunnel}/whatsapp-webhook")
            checks_passed += 1
            print(f"\n  [INFO] NEXT STEP:")
            print(f"     1. Copy this URL: {public_tunnel}/whatsapp-webhook")
            print(f"     2. Go to: https://panel.whapi.cloud")
            print(f"     3. Settings -> Webhooks")
            print(f"     4. Add webhook with URL: {public_tunnel}/whatsapp-webhook")
            print(f"     5. Select event: messages.post")
            print(f"     6. Save and activate")
        else:
            print(f"  [WARN] ngrok is running but no HTTPS tunnel found")
            print(f"     Start ngrok with: ngrok http 8000")
    else:
        print(f"  [FAIL] ngrok web interface not accessible")
        print(f"     Start ngrok with: ngrok http 8000")
except:
    print(f"  [FAIL] ngrok is NOT running")
    print(f"     Start with: ngrok http 8000")
    print(f"     Then configure webhook in Whapi dashboard")

checks_total += 1

# Check 4: Test Whapi API connection
print(f"\n[CHECK 4] Testing Whapi API Connection...")
if settings.WHAPI_API_KEY and settings.WHAPI_API_KEY != "your_whapi_api_key_here":
    try:
        headers = {"Authorization": f"Bearer {settings.WHAPI_API_KEY}"}
        response = requests.get(f"{settings.WHAPI_BASE_URL or 'https://gate.whapi.cloud'}/channel", 
                               headers=headers, timeout=10)
        if response.status_code == 200:
            print(f"  [OK] Whapi API connection successful")
            channel_info = response.json()
            print(f"     Channel: {channel_info.get('name', 'Unknown')}")
            checks_passed += 1
        elif response.status_code == 401:
            print(f"  [FAIL] Whapi API authentication failed")
            print(f"     Check WHAPI_API_KEY in .env")
        else:
            print(f"  [FAIL] Whapi API error: {response.status_code}")
    except Exception as e:
        print(f"  [FAIL] Error connecting to Whapi: {e}")
else:
    print(f"  [SKIP] Skipping Whapi test (API key not configured)")

checks_total += 1

# Summary
print("\n" + "="*80)
print(f"VERIFICATION SUMMARY: {checks_passed}/{checks_total} checks passed")
print("="*80)

if checks_passed == checks_total:
    print("\n[OK] ALL CHECKS PASSED!")
    print("\nYour WhatsApp webhook is configured correctly.")
    print("\nNext steps:")
    print("  1. Make sure webhook is configured in Whapi dashboard")
    print("  2. Send a test WhatsApp message to your Whapi number")
    print("  3. Watch server logs for [WEBHOOK RECEIVED]")
else:
    print("\n[WARN] SOME CHECKS FAILED")
    print("\nPlease fix the issues above:")
    if not settings.WHAPI_API_KEY or settings.WHAPI_API_KEY == "your_whapi_api_key_here":
        print("  - Add WHAPI_API_KEY to .env")
    if not settings.WHAPI_PHONE_ID or settings.WHAPI_PHONE_ID == "your_whapi_phone_id_here":
        print("  - Add WHAPI_PHONE_ID to .env")
    print("  - Make sure server is running: uvicorn whatsapp_webhook_server:app --reload")
    print("  - Make sure ngrok is running: ngrok http 8000")
    print("  - Configure webhook in Whapi dashboard with ngrok URL")

print("\n" + "="*80)
