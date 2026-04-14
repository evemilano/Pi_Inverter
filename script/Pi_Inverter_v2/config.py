#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configurazione centralizzata del sistema di monitoraggio inverter.
Nessuna importazione di SenseHat, nessun I/O — solo costanti e path.
"""

import os
import sys

# -------------------- CONNESSIONE INVERTER --------------------
INVERTER_IP = "192.168.1.11"
MODBUS_PORT = 502
MODBUS_TIMEOUT = 5
MODBUS_UNIT_ID = 1

# -------------------- REGISTRI MODBUS --------------------
SOLAR_REGISTER = 32080          # Potenza attiva (i32, gain 1000 → watt)
DAILY_YIELD_REGISTER = 32114    # Produzione giornaliera (u32, gain 100 → kWh)
GRID_REGISTER = 37113           # Potenza rete/APC (i32, gain 1000 → watt, /1000 → kW)
REGISTER_COUNT = 2              # Tutti i registri usano 2 x 16-bit

# -------------------- TIMING --------------------
POLL_INTERVAL = 60              # Intervallo polling in secondi
INTER_READ_DELAY = 0.5          # Delay tra letture Modbus sequenziali (sicurezza SDongle)

# -------------------- ORARI GIORNO/NOTTE --------------------
DAY_START_HOUR = 6              # Inizio periodo diurno (06:00)
DAY_END_HOUR = 20               # Fine periodo diurno (20:00)
DAILY_YIELD_HOURS = [20, 21, 22]  # Ore di aggiornamento daily yield

# -------------------- COLORI LED --------------------
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)

# -------------------- PATH FILE --------------------
# I dati restano nella directory Pi_Inverter/ originale per compatibilita
_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Pi_Inverter")
_LOGS_DIR = os.path.join(_DATA_DIR, "logs")

SOLAR_CSV = os.path.join(_LOGS_DIR, "power_log.csv")
GRID_CSV = os.path.join(_LOGS_DIR, "power_cons_log.csv")
DAILY_ENERGY_JSON = os.path.join(_DATA_DIR, "last_daily_energy.json")
NETWORK_WATCHDOG_LOG = os.path.join(_LOGS_DIR, "network_watchdog.log")

# -------------------- SERVICE SYSTEMD --------------------
SERVICE_FILE_PATH = "/etc/systemd/system/rbp4_8gb_inverter.service"
SERVICE_NAME = "rbp4_8gb_inverter.service"
PYTHON_EXEC = sys.executable
SCRIPT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "rbp4_8gb_inverter.py"))

# -------------------- NETWORK WATCHDOG --------------------
WATCHDOG_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "network_watchdog_config.json")
