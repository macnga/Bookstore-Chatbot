# version 25.12.2025
# Worker.py - clean up DB

# Clean up DB
import time
import database
from datetime import datetime
import os
import sys

if not os.path.exists(database.DB_PATH):
    print("Database not found, skipping cleanup.")
    sys.exit(1)

print("Starting database cleanup...")

def run_worker():
    while True:
        try:
            current_time = datetime.now().strftime('%H:%M:%S')

            c_confirm = database.cleaning_timeout_order(timeout_min=2)
            if c_confirm > 0:
                print(f"[{current_time}] Cleaned {c_confirm} unconfirmed orders.")

            c_purge = database.purge_old_orders(days=5)
            if c_purge > 0:
                print(f"[{current_time}] Purged {c_purge} old orders.")
            
            print(".", end="", flush=True)

            # Nghỉ 1h trước khi quét lại
            time.sleep(3600)

        except KeyboardInterrupt:
            print("\n🛑 Dừng Worker.")
            break
        except Exception as e:
            print(f"\n❌ Lỗi Worker: {e}")
            time.sleep(10)

if __name__ == "__main__":
    run_worker()
