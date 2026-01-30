import time
import os
import django
from django.core.management import call_command

# --- Django Setup ---
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.utils import timezone
from news.utils import is_in_fomc_critical_window, update_next_run_time

import argparse
import sys
from datetime import datetime

def run_scheduler(mock_now=None):
    print("--- 🗓️ Intelligent Scheduler Started ---")
    print("   [Standard] Daily at 08:00 UTC")
    print("   [Critical] Every 3 hours (24h window around FOMC)")
    
    if mock_now:
        print(f"   🧪 [TEST MODE] Simulating time: {mock_now}")

    last_run_critical = None
    last_run_daily = None

    while True:
        if mock_now:
            now = mock_now
        else:
            now = timezone.now()
            
        # This now returns the meeting datetime if critical, else None
        active_meeting = is_in_fomc_critical_window(now)
        is_critical = bool(active_meeting)

        if is_critical:
            # --- CRITICAL WINDOW LOGIC ---
            should_run = False
            if last_run_critical is None:
                should_run = True
            else:
                # Check if 3 hours have passed
                diff = now - last_run_critical
                if diff.total_seconds() >= (3 * 3600):
                    should_run = True

            if should_run:
                # Determine context
                if now < active_meeting:
                    context = "pre_announcement"
                else:
                    context = "post_announcement"
                
                fomc_str = active_meeting.strftime("%Y-%m-%d %H:%M")
                now_str = now.strftime("%Y-%m-%d %H:%M")
                
                print(f"\n🚨 [CRITICAL MODE] Running Scheduler at {now} (UTC)...")
                print(f"   Context: {context}, FOMC: {fomc_str}")
                
                try:
                    call_command(
                        "test_scheduler",
                        hours=3,
                        context=context,
                        fomc_time=fomc_str,
                        now=now_str
                    )
                except Exception as e:
                    print(f"Error running command: {e}")
                
                print("✅ [CRITICAL MODE] Finished.")
                last_run_critical = now
                last_run_daily = now 

        else:
            # --- STANDARD DAILY LOGIC ---
            should_run_daily = False
            
            if now.hour == 8:
                 if last_run_daily is None or last_run_daily.date() != now.date():
                      should_run_daily = True
            
            if should_run_daily:
                now_str = now.strftime("%Y-%m-%d %H:%M")
                print(f"\n☀️ [DAILY MODE] Running Scheduler at {now} (UTC)...")
                try:
                    call_command(
                        "test_scheduler", 
                        hours=24, 
                        context="general",
                        now=now_str
                    )
                except Exception as e:
                     print(f"Error running command: {e}")

                print("✅ [DAILY MODE] Finished.")
                last_run_daily = now
        
        # Update estimate
        try:
            update_next_run_time(last_run_critical, last_run_daily, is_critical)
        except Exception as e:
            print(f"Error updating metadata: {e}")
        
        # If testing with mock time, exit after one loop
        if mock_now:
            print("🧪 [TEST MODE] Single run complete. Exiting.")
            break

        # Check every minute
        time.sleep(60)



if __name__ == "__main__":
    import argparse
    import sys
    from datetime import datetime, timezone as dt_timezone
    parser = argparse.ArgumentParser(description="Run the intelligent scheduler.")
    parser.add_argument("--now", type=str, help="Simulate a specific time (YYYY-MM-DD HH:MM) for testing.")
    
    # Parse known args only to avoid conflict
    args, unknown = parser.parse_known_args()
    
    mock_dt = None
    if args.now:
        try:
            dt = datetime.strptime(args.now, "%Y-%m-%d %H:%M")
            mock_dt = timezone.make_aware(dt, dt_timezone.utc)
        except ValueError:
            print("Error: --now format must be 'YYYY-MM-DD HH:MM'")
            sys.exit(1)
            
    run_scheduler(mock_now=mock_dt)
