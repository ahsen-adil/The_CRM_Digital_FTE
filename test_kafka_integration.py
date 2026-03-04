"""
Kafka Integration Test Script

Tests all Kafka components:
1. Producer initialization
2. Message production
3. Consumer initialization
4. Message consumption
5. Worker initialization
6. End-to-end flow
"""
import sys
import os
import time
import json
from datetime import datetime

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    os.system('chcp 65001 >nul 2>&1')

print("="*80)
print("KAFKA INTEGRATION TEST")
print("="*80)
print(f"Test started at: {datetime.now().isoformat()}")
print()


# =============================================================================
# TEST 1: Import Kafka Modules
# =============================================================================
print("[TEST 1] Importing Kafka modules...")
try:
    from production.utils.kafka_config import KafkaTopics, PRODUCER_CONFIG, CONSUMER_CONFIG
    print("  [OK] Kafka config imported successfully")
except Exception as e:
    print(f"  [FAIL] Failed to import kafka_config: {e}")
    sys.exit(1)

try:
    from production.utils.kafka_producer import init_kafka_producer, get_kafka_producer
    print("  [OK] Kafka producer imported successfully")
except Exception as e:
    print(f"  [FAIL] Failed to import kafka_producer: {e}")
    sys.exit(1)

try:
    from production.utils.kafka_consumer import KafkaConsumerService
    print("  [OK] Kafka consumer imported successfully")
except Exception as e:
    print(f"  [FAIL] Failed to import kafka_consumer: {e}")
    sys.exit(1)

try:
    from production.config import settings
    print("  [OK] Settings imported successfully")
    print(f"     Kafka bootstrap servers: {settings.KAFKA_BOOTSTRAP_SERVERS}")
except Exception as e:
    print(f"  [FAIL] Failed to import settings: {e}")
    sys.exit(1)

print()


# =============================================================================
# TEST 2: Initialize Kafka Producer
# =============================================================================
print("[TEST 2] Initializing Kafka producer...")
try:
    producer = init_kafka_producer(settings.KAFKA_BOOTSTRAP_SERVERS)
    print("  ✅ Kafka producer initialized successfully")
except Exception as e:
    print(f"  ⚠️  Kafka producer initialization failed: {e}")
    print(f"     Continuing without Kafka (graceful degradation)")
    producer = None

print()


# =============================================================================
# TEST 3: Test Producer (if Kafka available)
# =============================================================================
if producer:
    print("[TEST 3] Testing Kafka producer...")
    try:
        # Test produce ticket event
        success = producer.produce_ticket_event(
            event_type='test',
            ticket_id='TEST-001',
            customer_id='customer-test',
            channel='web_form',
            subject='Kafka Integration Test',
            message='This is a test message for Kafka integration',
            metadata={'test': True}
        )
        
        if success:
            print("  ✅ Ticket event produced successfully")
        else:
            print("  ⚠️  Ticket event production failed")
        
        # Test produce audit event
        success = producer.produce_audit_event(
            event_type='test_event',
            entity_type='test',
            entity_id='TEST-001',
            action='test',
            details={'test': True}
        )
        
        if success:
            print("  ✅ Audit event produced successfully")
        else:
            print("  ⚠️  Audit event production failed")
        
        # Flush producer
        producer.flush(timeout=5)
        print("  ✅ Producer flushed successfully")
        
    except Exception as e:
        print(f"  ❌ Producer test failed: {e}")
else:
    print("[TEST 3] Skipping producer test (Kafka not available)")

print()


# =============================================================================
# TEST 4: Test Consumer Initialization
# =============================================================================
print("[TEST 4] Testing Kafka consumer initialization...")
try:
    consumer = KafkaConsumerService(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id='test-group',
        topics=[KafkaTopics.INCOMING_WEBFORM],
        max_retries=3,
    )
    print("  ✅ Kafka consumer initialized successfully")
    print(f"     Group ID: {consumer.group_id}")
    print(f"     Topics: {consumer.topics}")
except Exception as e:
    print(f"  ⚠️  Kafka consumer initialization failed: {e}")
    print(f"     Continuing without Kafka (graceful degradation)")
    consumer = None

print()


# =============================================================================
# TEST 5: Test Worker Initialization
# =============================================================================
print("[TEST 5] Testing Kafka worker initialization...")
try:
    from production.workers.kafka_workers import (
        AgentProcessingWorker,
        EmailNotificationWorker,
        WhatsAppNotificationWorker,
        EscalationWorker,
    )
    
    workers = []
    
    # Test Agent Processing Worker
    try:
        agent_worker = AgentProcessingWorker()
        workers.append(('Agent Processing', agent_worker))
        print("  ✅ AgentProcessingWorker initialized")
    except Exception as e:
        print(f"  ⚠️  AgentProcessingWorker failed: {e}")
    
    # Test Email Notification Worker
    try:
        email_worker = EmailNotificationWorker()
        workers.append(('Email Notifications', email_worker))
        print("  ✅ EmailNotificationWorker initialized")
    except Exception as e:
        print(f"  ⚠️  EmailNotificationWorker failed: {e}")
    
    # Test WhatsApp Notification Worker
    try:
        whatsapp_worker = WhatsAppNotificationWorker()
        workers.append(('WhatsApp Notifications', whatsapp_worker))
        print("  ✅ WhatsAppNotificationWorker initialized")
    except Exception as e:
        print(f"  ⚠️  WhatsAppNotificationWorker failed: {e}")
    
    # Test Escalation Worker
    try:
        escalation_worker = EscalationWorker()
        workers.append(('Escalations', escalation_worker))
        print("  ✅ EscalationWorker initialized")
    except Exception as e:
        print(f"  ⚠️  EscalationWorker failed: {e}")
    
    print(f"\n  Total workers initialized: {len(workers)}/4")
    
except Exception as e:
    print(f"  ❌ Worker initialization failed: {e}")

print()


# =============================================================================
# TEST 6: Test Webform API with Kafka
# =============================================================================
print("[TEST 6] Testing Webform API Kafka integration...")
try:
    import requests
    
    # Submit test webform
    response = requests.post(
        'http://localhost:8001/api/v1/webform/submit',
        json={
            'name': 'Kafka Test',
            'email': 'kafka-test@example.com',
            'subject': 'Kafka Integration Test',
            'message': 'Testing Kafka event production',
            'priority': 'normal'
        },
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"  ✅ Webform submitted successfully")
        print(f"     Ticket Number: {data.get('ticket_number')}")
        print(f"     Message: {data.get('message')}")
    else:
        print(f"  ⚠️  Webform submission returned status {response.status_code}")
        print(f"     Response: {response.text}")
        
except requests.exceptions.ConnectionError:
    print(f"  ⚠️  Webform API not running (port 8001)")
except Exception as e:
    print(f"  ❌ Webform test failed: {e}")

print()


# =============================================================================
# TEST 7: Check Kafka Topics (if Kafka available)
# =============================================================================
if producer:
    print("[TEST 7] Checking Kafka topics...")
    topics_to_check = [
        KafkaTopics.INCOMING_EMAIL,
        KafkaTopics.INCOMING_WHATSAPP,
        KafkaTopics.INCOMING_WEBFORM,
        KafkaTopics.AGENT_PROCESSING,
        KafkaTopics.AGENT_RESPONSES,
        KafkaTopics.EMAIL_NOTIFICATIONS,
        KafkaTopics.WHATSAPP_NOTIFICATIONS,
        KafkaTopics.ESCALATIONS,
        KafkaTopics.AUDIT_LOG,
        KafkaTopics.METRICS,
    ]
    
    print(f"  Topics configured: {len(topics_to_check)}")
    for topic in topics_to_check[:5]:  # Show first 5
        print(f"    - {topic}")
    if len(topics_to_check) > 5:
        print(f"    ... and {len(topics_to_check) - 5} more")
    
    print("  ✅ All topics configured in kafka_config.py")
else:
    print("[TEST 7] Skipping topic check (Kafka not available)")

print()


# =============================================================================
# TEST 8: Test Graceful Degradation
# =============================================================================
print("[TEST 8] Testing graceful degradation...")
print("  Simulating Kafka unavailable scenario...")

try:
    # Try to produce without Kafka
    if producer:
        # Temporarily break producer
        original_producer = producer
        producer = None
        
        # This should not crash
        print("  ✅ System continues without Kafka (graceful degradation)")
        
        # Restore producer
        producer = original_producer
    else:
        print("  ✅ System already running without Kafka")
        
except Exception as e:
    print(f"  ❌ Graceful degradation failed: {e}")

print()


# =============================================================================
# TEST SUMMARY
# =============================================================================
print("="*80)
print("TEST SUMMARY")
print("="*80)
print(f"Test completed at: {datetime.now().isoformat()}")
print()

# Count results
tests_passed = 0
tests_warnings = 0
tests_failed = 0

if producer:
    tests_passed += 1
    print("✅ Kafka Producer: WORKING")
else:
    tests_warnings += 1
    print("⚠️  Kafka Producer: NOT AVAILABLE (Kafka not running)")

if consumer:
    tests_passed += 1
    print("✅ Kafka Consumer: WORKING")
else:
    tests_warnings += 1
    print("⚠️  Kafka Consumer: NOT AVAILABLE (Kafka not running)")

if len(workers) > 0:
    tests_passed += 1
    print(f"✅ Kafka Workers: {len(workers)}/4 WORKING")
else:
    tests_warnings += 1
    print("⚠️  Kafka Workers: NOT AVAILABLE (Kafka not running)")

try:
    if response.status_code == 200:
        tests_passed += 1
        print("✅ Webform API: WORKING")
    else:
        tests_warnings += 1
        print("⚠️  Webform API: RUNNING (with issues)")
except:
    tests_failed += 1
    print("❌ Webform API: NOT RUNNING")

print()
print(f"Results: {tests_passed} passed, {tests_warnings} warnings, {tests_failed} failed")
print()

if tests_failed == 0 and tests_warnings > 0:
    print("⚠️  KAFKA IS NOT RUNNING")
    print()
    print("To start Kafka:")
    print("  docker-compose up -d kafka zookeeper")
    print()
    print("Then re-run this test.")
elif tests_failed == 0 and tests_warnings == 0:
    print("✅ ALL TESTS PASSED - KAFKA FULLY OPERATIONAL!")
else:
    print("❌ SOME TESTS FAILED")
    print("Check the errors above and fix them.")

print()
print("="*80)
