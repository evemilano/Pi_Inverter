#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entry point — monitoraggio inverter Huawei SUN2000-6KTL-M1.
Raspberry Pi 4 (8GB) con SenseHat.

Uso:
    sudo /home/pi/Python/script/Pi_Inverter/venv/bin/python \
         /home/pi/Python/script/Pi_Inverter_v2/rbp4_8gb_inverter.py

Servizio systemd:
    sudo systemctl restart rbp4_8gb_inverter.service
"""

import os
import sys
import threading
import time
from datetime import datetime, timedelta

# Aggiungi la directory padre al path per gli import relativi del package
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from Pi_Inverter_v2 import config
from Pi_Inverter_v2.core.sense_hat_provider import get_sense_hat
from Pi_Inverter_v2.core import data_store
from Pi_Inverter_v2.orchestrator import Orchestrator
from Pi_Inverter_v2.service_manager import ServiceManager
from Pi_Inverter_v2.network_watchdog import NetworkWatchdog


def daily_cleanup():
    """
    Thread di pulizia CSV giornaliera a mezzanotte.
    NESSUN uso di SenseHat — solo print per logging.
    """
    while True:
        now = datetime.now()
        next_cleanup = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        sleep_time = (next_cleanup - now).total_seconds()
        time.sleep(sleep_time)

        # Pulisci entrambi i file CSV
        data_store.cleanup_csv(config.SOLAR_CSV)
        data_store.cleanup_csv(config.GRID_CSV)


def main():
    """Funzione principale: inizializza componenti e avvia il loop."""
    sense = get_sense_hat()

    # --- Service file systemd ---
    if os.geteuid() == 0:
        service_manager = ServiceManager()
        if service_manager.create_service_file():
            sense.show_message("Service file OK", text_colour=config.GREEN, scroll_speed=0.03)
        else:
            sense.show_message("Errore service file", text_colour=config.RED, scroll_speed=0.03)
    else:
        sense.show_message("Non root: service file non creato",
                           text_colour=config.RED, scroll_speed=0.03)

    # --- Thread cleanup CSV (mezzanotte) ---
    cleanup_thread = threading.Thread(target=daily_cleanup, daemon=True)
    cleanup_thread.start()

    # --- Network Watchdog ---
    network_watchdog = NetworkWatchdog(
        check_interval=60,
        max_failures=10,
        ping_timeout=5,
        enable_reboot=True,
        config_file=config.WATCHDOG_CONFIG_FILE
    )
    network_watchdog.start()
    sense.show_message("Watchdog attivato", text_colour=config.GREEN, scroll_speed=0.03)

    # --- Messaggio di avvio ---
    sense.show_message(
        f"Inverter monitor v2 avviato. Polling {config.POLL_INTERVAL}s.",
        text_colour=config.GREEN, scroll_speed=0.03)

    # --- Loop principale ---
    orchestrator = Orchestrator()

    try:
        orchestrator.run()
    except KeyboardInterrupt:
        print("Arresto manuale.")
    finally:
        sense.clear()
        print("LED spenti. Fine.")


if __name__ == "__main__":
    main()
