#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Orchestrator — loop principale unificato giorno/notte.
Sostituisce DaytimeMonitor + NighttimeMonitor con un unico flusso.
Il logging della rete avviene 24/7 (fix del buco dati notturno).
"""

import time
from datetime import datetime

from . import config
from .core.modbus_client import ModbusSession
from .core import data_store
from .monitors import solar_monitor, grid_monitor, daily_yield_monitor
from .display.led_controller import LEDController


class Orchestrator:
    def __init__(self):
        self.led = LEDController()
        self.last_daily_yield = daily_yield_monitor.get_last_daily_yield()
        print(f"Orchestrator inizializzato. Daily yield: {self.last_daily_yield} kWh")

    def run(self):
        """Loop principale — gira fino a interruzione."""
        while True:
            start_time = time.time()

            try:
                self._poll_cycle()
            except Exception as e:
                print(f"Errore nel ciclo di polling: {e}")

            # Timing corretto: sottrai il tempo trascorso (sia giorno che notte)
            elapsed = time.time() - start_time
            sleep_time = max(0, config.POLL_INTERVAL - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

    def _poll_cycle(self):
        """Singolo ciclo di polling: lettura, logging, display."""
        now = datetime.now()
        timestamp = now.strftime("%Y_%m_%d_%H:%M")
        is_daytime = config.DAY_START_HOUR <= now.hour < config.DAY_END_HOUR

        # Imposta luminosita LED
        self.led.set_low_light(not is_daytime)

        # --- Letture Modbus con sessione condivisa ---
        solar_power = 0
        grid_power = 0.0

        try:
            with ModbusSession() as client:
                # SEMPRE: leggi potenza rete (24/7)
                grid_power = grid_monitor.read(client)
                time.sleep(config.INTER_READ_DELAY)

                if is_daytime:
                    # Giorno: leggi anche potenza solare
                    solar_power = solar_monitor.read(client)
                else:
                    # Notte: aggiorna daily yield se nelle ore giuste
                    if daily_yield_monitor.update_if_needed(client):
                        self.last_daily_yield = daily_yield_monitor.get_last_daily_yield()

        except ConnectionError as e:
            print(f"Connessione Modbus fallita: {e}")
        except Exception as e:
            print(f"Errore lettura Modbus: {e}")

        # --- Logging CSV (rete SEMPRE, solare solo di giorno) ---
        data_store.append_reading(config.GRID_CSV, timestamp, round(grid_power, 3))

        if is_daytime:
            data_store.append_reading(config.SOLAR_CSV, timestamp, solar_power)

        # --- Aggiorna il valore corrente della rete nel LED controller ---
        self.led.current_grid_power = grid_power

        # --- Display ---
        if is_daytime:
            self._display_daytime(solar_power, grid_power)
        else:
            self._display_nighttime(grid_power)

    def _display_daytime(self, solar_power, grid_power):
        """Sequenza display diurna: testo + doppia barra animata."""
        # Leggi TUTTI i valori storici per il calcolo corretto del 98° percentile
        solar_historical = data_store.read_all_values(config.SOLAR_CSV)
        grid_historical = data_store.read_all_values(config.GRID_CSV)

        solar_level = self.led.calculate_level(solar_power, solar_historical)
        grid_level = self.led.calculate_level(grid_power, grid_historical)
        solar_color = self.led.choose_color(solar_power, solar_historical)

        # Messaggi scrollanti
        self.led.show_message(f"Sol: {solar_power / 1000:.1f} kW",
                              color=solar_color, scroll_speed=0.06)
        self.led.show_message(
            f"Rete: {grid_power:.1f} kW",
            color=config.BLUE if grid_power >= 0 else config.RED,
            scroll_speed=0.06)

        # Doppia barra animata (solare + rete)
        self.led.update_dual_bars(solar_level, grid_level, solar_color)

    def _display_nighttime(self, grid_power):
        """Sequenza display notturna: daily yield + barra rete + grafico giornaliero."""
        # 1. Testo daily yield
        self.led.clear()
        text = f"Daily power: {self.last_daily_yield:.2f} kWh"
        self.led.show_message(text, color=config.WHITE, scroll_speed=0.06)
        self.led.show_message(text, color=config.WHITE, scroll_speed=0.06)
        time.sleep(1)

        # 2. Barra consumo rete
        grid_historical = data_store.read_all_values(config.GRID_CSV)
        grid_level = self.led.calculate_level(grid_power, grid_historical)

        self.led.show_message(
            f"Rete: {grid_power:.1f} kW",
            color=config.BLUE if grid_power >= 0 else config.RED,
            scroll_speed=0.06)
        self.led.update_single_bar(grid_level, color_mode='auto')
        time.sleep(1)

        # 3. Grafico produzione giornaliera
        bar_values = data_store.get_day_power_chart(
            config.SOLAR_CSV,
            num_bars=8,
            day_start_hour=config.DAY_START_HOUR,
            day_end_hour=config.DAY_END_HOUR
        )
        self.led.update_bar_chart(bar_values, config.GREEN)
