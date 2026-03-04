"""
Initialize Database Schema

Creates all required tables for the email polling system.
"""
import psycopg2
from production.config import settings

print("="*80)
print("DATABASE SCHEMA INITIALIZATION")
print("="*80)

try:
    # Connect
    print("\n[1/2] Connecting to database...")
    conn = psycopg2.connect(settings.DATABASE_URL, sslmode='require')
    print("[OK] Connected")
    
    # Drop existing tables
    print("\n[1/3] Dropping existing tables...")
    with conn.cursor() as cur:
        cur.execute("""
            DROP TABLE IF EXISTS ai_interactions CASCADE;
            DROP TABLE IF EXISTS escalations CASCADE;
            DROP TABLE IF EXISTS messages CASCADE;
            DROP TABLE IF EXISTS tickets CASCADE;
            DROP TABLE IF EXISTS conversations CASCADE;
            DROP TABLE IF EXISTS customers CASCADE;
            DROP TABLE IF EXISTS knowledge_base CASCADE;
            DROP TABLE IF EXISTS ticket_counters CASCADE;
        """)
    conn.commit()
    print("[OK] Tables dropped")
    
    # Read schema
    print("\n[2/3] Reading schema.sql...")
    with open('production/database/schema.sql', 'r', encoding='utf-8') as f:
        schema = f.read()
    
    # Execute
    print("[OK] Executing schema...")
    with conn.cursor() as cur:
        cur.execute(schema)
    conn.commit()
    print("[OK] Schema created successfully!")
    
    conn.close()
    
    print("\n" + "="*80)
    print("DATABASE READY")
    print("="*80)
    print("\nTables created:")
    print("  - customers")
    print("  - conversations")
    print("  - tickets")
    print("  - messages")
    print("  - escalations")
    print("  - knowledge_base")
    print("  - ticket_counters")
    print("  - ai_interactions")
    print("\nNow run: python poll_emails_sync.py")
    
except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
