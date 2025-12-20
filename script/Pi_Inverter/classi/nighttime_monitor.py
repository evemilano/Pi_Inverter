#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .inverter_monitor import InverterMonitor
from .led_controller import LEDController
from .csv_handler import CSVHandler
from .apc_monitor import APCMonitor
import time
import os

class NighttimeMonitor:
    def __init__(self, sense, inverter_monitor):
        self.sense = sense
        self.inverter_monitor = inverter_monitor
        self.display_counter = 0  # Per alternare tra grafico e testo
        self.led_controller = LEDController()
        self.csv_handler = CSVHandler(self.inverter_monitor.csv_filepath)

        # Aggiungi APC monitor e grid CSV handler per la barra rete
        self.apc_monitor = APCMonitor()
        self.grid_csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "power_cons_log.csv")
        self.grid_csv_handler = CSVHandler(self.grid_csv_path)
        
        # Leggi il valore dal file JSON all'inizializzazione
        value = self.inverter_monitor.read_daily_power_from_file()
        if value is not None:
            self.last_daily_yield = value
        else:
            self.last_daily_yield = 0.0
        print(f"NighttimeMonitor inizializzato con daily yield: {self.last_daily_yield} kWh")
        self.sense.show_message(f"NighttimeMonitor inizializzato con daily yield: {self.last_daily_yield} kWh", 
                                 text_colour=self.led_controller.GREEN, scroll_speed=0.03)

    def update(self):
        """Aggiorna il display durante la notte"""
        # Prova ad aggiornare il valore giornaliero alle ore specificate
        if self.inverter_monitor.update_daily_yield():
            # Se aggiornato, leggi il nuovo valore
            value = self.inverter_monitor.read_daily_power_from_file()
            if value is not None:
                self.last_daily_yield = value
                print(f"Daily yield aggiornato: {self.last_daily_yield} kWh")
                self.sense.show_message(f"Daily yield aggiornato: {self.last_daily_yield} kWh",
                                 text_colour=self.led_controller.GREEN, scroll_speed=0.03)

        # Sequenza di visualizzazione notturna: Testo → Barra Rete → Grafico
        self.display_daily_yield()
        time.sleep(1)

        self.display_grid_bar()
        time.sleep(1)

        self.display_graph()

    def display_daily_yield(self):
        """Mostra il valore di produzione giornaliera"""
        self.sense.clear()
        text = f"Daily power: {self.last_daily_yield:.2f} kWh"
        self.led_controller.show_message(text, color=(255, 255, 255), scroll_speed=0.06)
        self.led_controller.show_message(text, color=(255, 255, 255), scroll_speed=0.06)

    def display_grid_bar(self):
        """Mostra la barra di consumo rete a 8 colonne con effetto onda"""
        # Ottieni il consumo corrente dalla rete
        grid_power = self.apc_monitor.get_power_consumption()

        # Aggiorna il valore corrente nel LED controller
        self.led_controller.current_grid_power = grid_power

        # Ottieni i dati storici della rete
        grid_historical = [p for _, p in self.grid_csv_handler.read_csv_data()]

        # Calcola il livello della barra (1-8) rispetto ai valori storici
        grid_level = self.led_controller.calculate_level(grid_power, grid_historical)

        # Mostra il messaggio con il valore
        self.led_controller.show_message(f"Rete: {grid_power:.1f} kW",
                                      color=self.led_controller.BLUE if grid_power >= 0 else self.led_controller.RED,
                                      scroll_speed=0.06)

        # Mostra la barra full-width con effetto onda (colore auto in base al segno)
        self.led_controller.update_single_bar(grid_level, color_mode='auto')

    def display_graph(self):
        """Mostra il grafico delle potenze notturne"""
        # Ottieni i valori del grafico a barre dai dati del giorno
        bar_values = self.csv_handler.get_day_power_chart(
            num_bars=8,
            day_start_hour=self.inverter_monitor.DAY_START_HOUR,
            day_end_hour=self.inverter_monitor.DAY_END_HOUR
        )
        # Aggiorna il grafico a barre con i valori del giorno
        self.led_controller.update_bar_chart(bar_values, (0, 255, 0)) 