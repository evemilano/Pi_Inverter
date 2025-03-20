#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .inverter_monitor import InverterMonitor
from .led_controller import LEDController
from .csv_handler import CSVHandler
import time

class NighttimeMonitor:
    def __init__(self, sense, inverter_monitor):
        self.sense = sense
        self.inverter_monitor = inverter_monitor
        self.display_counter = 0  # Per alternare tra grafico e testo
        self.led_controller = LEDController()
        self.csv_handler = CSVHandler(self.inverter_monitor.csv_filepath)
        
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

        # Mostra prima il grafico, poi immediatamente il testo, senza pause lunghe
        self.display_graph()
        
        # Pausa breve di 1 secondo per separare le visualizzazioni
        time.sleep(1)
        
        # Mostra il valore di produzione giornaliera
        self.display_daily_yield()
        
        # Dopo aver mostrato il testo, rimostra subito il grafico
        self.display_graph()

    def display_daily_yield(self):
        """Mostra il valore di produzione giornaliera"""
        self.sense.clear()
        text = f"Daily power: {self.last_daily_yield:.2f} kWh"
        self.led_controller.show_message(text, color=(255, 255, 255), scroll_speed=0.06)
        self.led_controller.show_message(text, color=(255, 255, 255), scroll_speed=0.06)

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