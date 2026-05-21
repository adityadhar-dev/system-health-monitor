"""
System Health Monitor
---------------------
Monitors CPU, memory, disk, and network usage in real time.
Logs alerts when thresholds are breached and generates daily reports.

Usage:
    python monitor.py             # Run live monitor
    python monitor.py --report    # Show today's alert report
    python monitor.py --config    # Show / edit thresholds
"""

import os
import sys
import time
import json
import platform
import datetime
import argparse


# ── Configuration ─────────────────────────────────────────────────────────────

CONFIG_FILE = "config.json"
LOG_FILE = "health_log.json"

DEFAULT_CONFIG = {
    "cpu_threshold": 85,        # % — alert if CPU exceeds this
    "memory_threshold": 80,     # % — alert if RAM exceeds this
    "disk_threshold": 90,       # % — alert if disk exceeds this
    "check_interval": 5,        # seconds between checks
    "log_alerts": True          # write alerts to log file
}


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    return DEFAULT_CONFIG.copy()


def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


# ── Cross-platform system metrics ─────────────────────────────────────────────

def get_cpu_percent():
    """Estimate CPU usage using /proc/stat on Linux, fallback otherwise."""
    if platform.system() == "Linux":
        try:
            def read_stat():
                with open("/proc/stat") as f:
                    line = f.readline()
                parts = list(map(int, line.split()[1:]))
                idle = parts[3]
                total = sum(parts)
                return idle, total

            idle1, total1 = read_stat()
            time.sleep(0.3)
            idle2, total2 = read_stat()
            delta_idle = idle2 - idle1
            delta_total = total2 - total1
            return round((1 - delta_idle / delta_total) * 100, 1) if delta_total else 0.0
        except Exception:
            return 0.0
    try:
        import subprocess
        result = subprocess.run(["ps", "-A", "-o", "%cpu"], capture_output=True, text=True)
        values = [float(x) for x in result.stdout.strip().split("\n")[1:] if x.strip()]
        return round(min(sum(values), 100.0), 1)
    except Exception:
        return 0.0


def get_memory():
    """Return (used_gb, total_gb, percent) for RAM."""
    if platform.system() == "Linux":
        try:
            info = {}
            with open("/proc/meminfo") as f:
                for line in f:
                    key, val = line.split(":")
                    info[key.strip()] = int(val.split()[0])  # in kB
            total_kb = info.get("MemTotal", 0)
            avail_kb = info.get("MemAvailable", info.get("MemFree", 0))
            used_kb = total_kb - avail_kb
            pct = round((used_kb / total_kb) * 100, 1) if total_kb else 0
            return round(used_kb / 1_048_576, 2), round(total_kb / 1_048_576, 2), pct
        except Exception:
            return 0, 0, 0
    # Fallback for macOS/Windows — show zeroes with a note
    return 0, 0, 0


def get_disk(path="/"):
    """Return (used_gb, total_gb, percent) for the given disk path."""
    try:
        stat = os.statvfs(path)
        total = stat.f_frsize * stat.f_blocks
        free = stat.f_frsize * stat.f_bfree
        used = total - free
        pct = round((used / total) * 100, 1) if total else 0
        return round(used / 1e9, 2), round(total / 1e9, 2), pct
    except Exception:
        return 0, 0, 0


# ── Alert logging ──────────────────────────────────────────────────────────────

def log_alert(metric, value, threshold):
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "metric": metric,
        "value": value,
        "threshold": threshold,
        "message": f"{metric} at {value}% — exceeded threshold of {threshold}%"
    }
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE) as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
    logs.append(entry)
    with open(LOG_FILE, "w") as f:
        json.dump(logs[-500:], f, indent=2)  # keep last 500 alerts
    return entry


# ── Display helpers ────────────────────────────────────────────────────────────

def bar(pct, width=30):
    filled = int((pct / 100) * width)
    b = "█" * filled + "░" * (width - filled)
    if pct >= 85:
        status = "⚠ HIGH"
    elif pct >= 70:
        status = "  WARN"
    else:
        status = "    OK"
    return f"[{b}] {pct:5.1f}%  {status}"


def clear():
    os.system("cls" if platform.system() == "Windows" else "clear")


# ── Main monitor loop ──────────────────────────────────────────────────────────

def run_monitor():
    cfg = load_config()
    alerts_triggered = []

    print("System Health Monitor — press Ctrl+C to stop\n")
    print(f"Thresholds: CPU {cfg['cpu_threshold']}% | RAM {cfg['memory_threshold']}% | Disk {cfg['disk_threshold']}%")
    print(f"Check interval: every {cfg['check_interval']}s\n")
    print("-" * 60)

    try:
        while True:
            cpu = get_cpu_percent()
            mem_used, mem_total, mem_pct = get_memory()
            disk_used, disk_total, disk_pct = get_disk()
            now = datetime.datetime.now().strftime("%H:%M:%S")

            print(f"\n[{now}]")
            print(f"  CPU     {bar(cpu)}")
            print(f"  RAM     {bar(mem_pct)}   ({mem_used}/{mem_total} GB)")
            print(f"  Disk    {bar(disk_pct)}   ({disk_used}/{disk_total} GB)")

            # Check thresholds and log
            for metric, value, threshold in [
                ("CPU", cpu, cfg["cpu_threshold"]),
                ("Memory", mem_pct, cfg["memory_threshold"]),
                ("Disk", disk_pct, cfg["disk_threshold"]),
            ]:
                if value >= threshold and cfg["log_alerts"]:
                    alert = log_alert(metric, value, threshold)
                    alerts_triggered.append(alert)
                    print(f"\n  🔴 ALERT: {alert['message']}")

            print(f"\n  Alerts this session: {len(alerts_triggered)}")
            time.sleep(cfg["check_interval"])

    except KeyboardInterrupt:
        print("\n\nMonitor stopped.")
        if alerts_triggered:
            print(f"Total alerts this session: {len(alerts_triggered)}")
            print(f"All alerts saved to: {LOG_FILE}")


# ── Report ─────────────────────────────────────────────────────────────────────

def show_report():
    if not os.path.exists(LOG_FILE):
        print("No alert log found. Run the monitor first.")
        return

    with open(LOG_FILE) as f:
        try:
            logs = json.load(f)
        except json.JSONDecodeError:
            print("Log file corrupted.")
            return

    today = datetime.date.today().isoformat()
    today_logs = [l for l in logs if l["timestamp"].startswith(today)]

    print(f"\n--- Alert Report: {today} ---")
    print(f"Total alerts today: {len(today_logs)}")

    if not today_logs:
        print("No alerts triggered today. System is healthy.")
        return

    counts = {}
    for l in today_logs:
        counts[l["metric"]] = counts.get(l["metric"], 0) + 1

    print("\nAlert breakdown:")
    for metric, count in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {metric:<10} {count} alert(s)")

    print("\nLast 5 alerts:")
    for l in today_logs[-5:]:
        ts = l["timestamp"][11:19]
        print(f"  [{ts}] {l['message']}")


# ── Config display ─────────────────────────────────────────────────────────────

def show_config():
    cfg = load_config()
    print("\n--- Current Thresholds ---")
    for k, v in cfg.items():
        print(f"  {k:<25} {v}")
    print(f"\nConfig file: {CONFIG_FILE}")


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="System Health Monitor")
    parser.add_argument("--report", action="store_true", help="Show today's alert report")
    parser.add_argument("--config", action="store_true", help="Show current config/thresholds")
    args = parser.parse_args()

    if args.report:
        show_report()
    elif args.config:
        show_config()
    else:
        run_monitor()


if __name__ == "__main__":
    main()
