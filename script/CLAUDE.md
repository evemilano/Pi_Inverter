# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Solar inverter monitoring system for a **Huawei SUN2000-6KTL-M1** running on a **Raspberry Pi 4 (8GB)** with **SenseHat** (8x8 RGB LED matrix). Written in Italian. Reads real-time solar production and grid consumption via **Modbus TCP** and displays status on the SenseHat LEDs.

## Running

The main script runs as a systemd service (`rbp4_8gb_inverter.service`) and requires root for service file creation:

```bash
# Run directly (with venv)
sudo /home/pi/Python/script/Pi_Inverter/venv/bin/python /home/pi/Python/script/Pi_Inverter/rbp4_8gb_inverter.py

# Service management
sudo systemctl restart rbp4_8gb_inverter.service
sudo systemctl status rbp4_8gb_inverter.service
```

Stand-alone test scripts in `stand_alone_/` can be run individually for testing specific components (LED effects, Modbus reads, daily energy, etc.).

## Architecture

**Entry point:** `Pi_Inverter/rbp4_8gb_inverter.py` — main loop that alternates between daytime (06:00–20:00) and nighttime (20:00–06:00) monitoring modes, polling every 60 seconds.

**Class hierarchy in `Pi_Inverter/classi/`:**

- `InverterMonitor` — base class: Modbus TCP connection to inverter at `192.168.1.11:502`, register reads (power: `32080`, daily yield: `32114`), daily energy JSON persistence
- `DaytimeMonitor` — daytime cycle: reads solar power + grid power, logs to CSV, updates LED matrix with dual bar chart (solar + grid)
- `NighttimeMonitor` — nighttime cycle: scrolling display of last daily yield, LED animations
- `APCMonitor` — reads grid consumption/export from Modbus register `37113` (Active Power Control), returns kW (positive = consuming, negative = exporting)
- `LEDController` — all SenseHat LED matrix operations: color gradients, bar charts, animations, message scrolling
- `CSVHandler` — CSV read/write/cleanup (auto-purges data older than 1 year), daily midnight cleanup thread
- `NetworkWatchdog` — background thread pinging gateway + public DNS; reboots system after configurable consecutive failures. Config in `network_watchdog_config.json`
- `ServiceManager` — creates/updates the systemd `.service` file

## Key Dependencies

- `pymodbus` — Modbus TCP client for inverter communication
- `sense_hat` — Raspberry Pi SenseHat library (LED matrix, sensors)
- Python venv at `Pi_Inverter/venv/`

## Data Files

- `Pi_Inverter/logs/power_log.csv` — solar production time series (timestamp, watts)
- `Pi_Inverter/logs/power_cons_log.csv` — grid consumption time series (timestamp, kW)
- `Pi_Inverter/last_daily_energy.json` — persisted daily yield (updated at hours 20–22)
- `Pi_Inverter/network_watchdog_config.json` — watchdog tuning (interval, max failures, hosts)
- `Pi_Inverter/logs/network_watchdog.log` — network watchdog log (connectivity checks, failures, reboots)

## Debugging

- Modbus read errors are logged via `print()` to stdout (not on the SenseHat LED) to avoid blocking the polling cycle
- View live errors with: `sudo journalctl -u rbp4_8gb_inverter.service -f`

## Notes

- All code comments and UI messages are in Italian
- The system runs headless on a Raspberry Pi; the only display is the 8x8 SenseHat LED matrix
- Modbus register values are signed 32-bit (two 16-bit registers, big-endian, two's complement)
- Grid power sign convention: positive = consuming from grid, negative = exporting to grid
- Modbus reads use a shared TCP connection per polling cycle (single connect → read solar → 0.5s delay → read grid → close) to reduce SDongle load
