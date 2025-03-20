#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script di test per verificare la visualizzazione notturna
"""

from sense_hat import SenseHat
from classi.inverter_monitor import InverterMonitor
from classi.nighttime_monitor import NighttimeMonitor
import time
import os
import json

def test_nighttime_display():
    """Test della visualizzazione notturna"""
    print("Inizializzazione del test...")
    
    # Inizializza i componenti
    inverter_monitor = InverterMonitor()
    nighttime_monitor = NighttimeMonitor(inverter_monitor.sense, inverter_monitor)
    
    print("Test della lettura del valore giornaliero dal file JSON...")
    
    # Verifica che il file esista
    if not os.path.exists(inverter_monitor.daily_energy_file):
        print(f"File {inverter_monitor.daily_energy_file} non trovato!")
        return
    
    # Leggi il valore dal file
    value = inverter_monitor.read_daily_power_from_file()
    if value is not None:
        print(f"Valore letto dal file: {value} kWh")
        
        # Test della visualizzazione
        nighttime_monitor.display_daily_yield()
        
        print("Test completato. Verifica che il display abbia mostrato:")
        print(f"Daily power: {value} kWh")
        print("(dovrebbe essere stato mostrato due volte)")
    else:
        print("Errore nella lettura del valore dal file")

if __name__ == "__main__":
    test_nighttime_display() 