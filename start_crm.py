"""
UNIFIED CRM STARTUP - RUNS ALL WORKING SERVICES

This script starts all services that are already working:
- poll_emails_sync.py (Email with AI + SMTP)
- whatsapp_webhook_kafka.py (WhatsApp with AI + Whapi)
- webform_api_v2.py (Webform with AI)
- api_server.py (API Server)

All in one command with unified logging.
"""
import subprocess
import sys
import os
import signal
import time
from datetime import datetime

# Change to script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Add script directory to Python path for all subprocesses
env = os.environ.copy()
python_path = script_dir
if 'PYTHONPATH' in env:
    python_path = f"{script_dir}{os.pathsep}{env['PYTHONPATH']}"
env['PYTHONPATH'] = python_path

print("="*80)
print("🚀 STARTING UNIFIED CRM SYSTEM")
print("="*80)
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Working Directory: {script_dir}")
print(f"PYTHONPATH: {python_path}")
print("="*80)
print()

# Services to start
services = {
    'Email Polling': 'python poll_emails_sync.py',
    'WhatsApp Webhook': 'python whatsapp_webhook_kafka.py',
    'Webform API': 'python webform_api_v2.py',
    'API Server': 'python api_server.py'
}

processes = []

def signal_handler(sig, frame):
    print("\n" + "="*80)
    print("🛑 SHUTTING DOWN CRM SYSTEM")
    print("="*80)
    print("Stopping services...")
    for proc in processes:
        if proc.poll() is None:
            proc.terminate()
            print(f"  ✅ Terminated")
    print("="*80)
    print("✅ CRM System stopped")
    print("="*80)
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

print("Starting services:")
print()

# Start each service
for name, command in services.items():
    print(f"Starting {name}...")
    try:
        proc = subprocess.Popen(
            command,
            shell=True,
            env=env,  # Use environment with PYTHONPATH
            cwd=script_dir  # Set working directory
        )
        processes.append(proc)
        print(f"  ✅ {name} started (PID: {proc.pid})")
        time.sleep(1)  # Stagger startups
    except Exception as e:
        print(f"  ❌ {name} failed: {e}")

print()
print("="*80)
print("✅ ALL SERVICES STARTED")
print("="*80)
print()
print("Services running:")
for i, (name, _) in enumerate(services.items(), 1):
    print(f"  {i}. {name}")
print()
print("Press Ctrl+C to stop all services")
print("="*80)
print()

# Keep running and monitor
try:
    while True:
        time.sleep(5)
        
        # Check if any process died
        for i, (name, _) in enumerate(services.items()):
            proc = processes[i]
            if proc.poll() is not None:
                print(f"⚠️  {name} exited with code {proc.poll()}")
                
except KeyboardInterrupt:
    signal_handler(None, None)
