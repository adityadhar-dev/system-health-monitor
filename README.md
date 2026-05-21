# System Health Monitor

A lightweight Python CLI tool that monitors CPU, memory, and disk usage in real time — no external dependencies required. Logs alerts when thresholds are breached and generates daily reports.

Built from hands-on experience managing multi-site IT infrastructure across server farms and manufacturing environments.

## Features

- Live monitoring of CPU, RAM, and disk usage with visual bar graphs
- Configurable alert thresholds per metric
- Alert logging to JSON — full history with timestamps
- Daily summary reports
- Zero external dependencies — pure Python standard library

## Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/system-health-monitor.git
cd system-health-monitor

# Run live monitor (default: checks every 5 seconds)
python monitor.py

# View today's alert report
python monitor.py --report

# Show current thresholds
python monitor.py --config
```

## Example Output

```
System Health Monitor — press Ctrl+C to stop

Thresholds: CPU 85% | RAM 80% | Disk 90%
Check interval: every 5s

------------------------------------------------------------

[14:32:07]
  CPU     [████████████░░░░░░░░░░░░░░░░░░]  42.0%      OK
  RAM     [████████████████████░░░░░░░░░░]  67.3%    WARN   (5.4/8.0 GB)
  Disk    [████████████████████████░░░░░░]  79.1%      OK   (237/300 GB)

  Alerts this session: 0
```

## Configuration

Edit `config.json` to customise thresholds:

```json
{
  "cpu_threshold": 85,
  "memory_threshold": 80,
  "disk_threshold": 90,
  "check_interval": 5,
  "log_alerts": true
}
```

## Tech Stack

- Python 3.x
- Standard library only: `os`, `sys`, `time`, `json`, `platform`, `datetime`, `argparse`

## Real-World Background

This project is inspired by monitoring infrastructure across 3 sites at a pharmaceutical manufacturing company — where server downtime has direct operational cost. The tool is deliberately minimal and dependency-free so it can run on any Linux server without setup overhead.

---

Built by Aditya Dhar | [LinkedIn](https://www.linkedin.com/in/aditya-dhar-777921242)
