"""
Test WhatsApp AI Agent Directly
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

print("="*80)
print("TESTING WHATSAPP AI AGENT")
print("="*80)
print()

# Test 1: Import
print("Test 1: Importing AI agent module...")
try:
    from production.agent.customer_success_agent import run_agent_sync
    print("[OK] Import successful")
except Exception as e:
    print(f"[FAIL] Import failed: {e}")
    sys.exit(1)

print()

# Test 2: Call AI agent
print("Test 2: Calling AI agent with test message...")
try:
    response = run_agent_sync(
        customer_email="923182710120@whatsapp.com",
        subject="WhatsApp Support",
        message_body="Hello, how are you?"
    )
    print("[OK] AI agent call successful")
    print()
    # Encode to avoid Windows console issues
    reply_text = response.reply_text.encode('utf-8', errors='ignore').decode('utf-8')
    print(f"Reply Text: {reply_text[:200]}...")
    print(f"Sentiment: {response.sentiment_score}")
    print(f"Confidence: {response.confidence_score}")
    print(f"Escalation: {response.escalation_required}")
    print()
except Exception as e:
    print(f"[FAIL] AI agent call failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("="*80)
print("AI AGENT IS WORKING CORRECTLY")
print("="*80)
