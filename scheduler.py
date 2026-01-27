import time
import os
import django
from django.core.management import call_command

# --- Django Setup ---
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

def run_scheduler():
    print("--- 🔬 MOCK Scheduler Started ---")
    print("Logic: Runs every minute. Critical = Minute is multiple of 5.")
    
    while True:
        call_command('test_scheduler')
        
        # Sleep for 1 minute for testing
        time.sleep(60)

if __name__ == "__main__":
    run_scheduler()
