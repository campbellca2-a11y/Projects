import psutil
import time
import datetime
import os
import cpuinfo

INTERVAL = 0.5  # seconds
SESSION_ID = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

DATA_DIR = f"data/sessions/{SESSION_ID}"
os.makedirs(DATA_DIR, exist_ok=True)

log_file = open(f"{DATA_DIR}/vitals.csv", "w")
log_file.write("timestamp,cpu_percent,ram_percent,cpu_freq\n")

cpu_name = cpuinfo.get_cpu_info().get("brand_raw", "Unknown CPU")

print("\n=== DIGITAL STETHOSCOPE ===")
print(f"CPU: {cpu_name}")
print(f"Session: {SESSION_ID}")
print("Press Ctrl+C to stop.\n")

last_cpu = 0

try:
    while True:
        timestamp = datetime.datetime.now().isoformat()
        cpu = psutil.cpu_percent(interval=None)
        delta = cpu - last_cpu
        last_cpu = cpu

        if delta > 15:
            print("\n⚠️  Spike detected:", f"+{delta:.1f}%")

        ram = psutil.virtual_memory().percent
        freq = psutil.cpu_freq().current if psutil.cpu_freq() else 0

        log_file.write(f"{timestamp},{cpu},{ram},{freq}\n")
        log_file.flush()

        bar = "#" * int(cpu / 2)

        print(
            f"\rCPU [{bar:<20}] {cpu:5.1f}% | "
            f"RAM {ram:5.1f}% | "
            f"Freq {freq:6.0f} MHz",
            end=""
        )

        time.sleep(INTERVAL)

except KeyboardInterrupt:
    print("\n\nSession ended.")
finally:
    log_file.close()
