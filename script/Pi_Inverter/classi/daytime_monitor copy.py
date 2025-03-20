#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from .inverter_monitor import InverterMonitor
from .led_controller import LEDController
from .csv_handler import CSVHandler
from .apc_monitor import APCMonitor

class DaytimeMonitor:
    def __init__(self, sense, inverter_monitor):
        self.sense = sense
        self.inverter_monitor = inverter_monitor
        self.led_controller = LEDController()
        self.csv_handler = CSVHandler(self.inverter_monitor.csv_filepath)
        self.apc_monitor = APCMonitor()
        self.grid_csv_handler = CSVHandler("power_cons_log.csv")

    def update(self):
        """Esegue il monitoraggio diurno."""
        now = datetime.now()
        timestamp = now.strftime("%Y_%m_%d_%H:%M")
        
        # Ottieni potenza solare
        solar_power = self.inverter_monitor.query_inverter()
        if solar_power is None:
            solar_power = 0
            
        # Ottieni potenza dalla rete
        grid_power = self.apc_monitor.get_power_consumption()
        
        # Salva i dati nei rispettivi file CSV
        self.csv_handler.append_to_csv(timestamp, solar_power)
        self.grid_csv_handler.append_to_csv(timestamp, grid_power)
        
        # Calcola i livelli per la visualizzazione
        solar_historical = [p for _, p in self.csv_handler.read_csv_data()]
        grid_historical = [p for _, p in self.grid_csv_handler.read_csv_data()]
        
        solar_level = self.led_controller.calculate_level(solar_power, solar_historical)
        grid_level = self.led_controller.calculate_level(grid_power, grid_historical)
        
        # Scegli il colore per la barra solare
        solar_color = self.led_controller.choose_color(solar_power, solar_historical)
        
        # Mostra i messaggi
        self.led_controller.show_message(f"Sol: {solar_power:,} W".replace(",", "."), 
                                      color=solar_color, scroll_speed=0.06)
        self.led_controller.show_message(f"Rete: {grid_power:.1f} kW", 
                                      color=self.led_controller.BLUE, scroll_speed=0.06)
        
        # Aggiorna la matrice LED con entrambe le barre
        self.led_controller.update_led_matrix(solar_level, grid_level, solar_color) 