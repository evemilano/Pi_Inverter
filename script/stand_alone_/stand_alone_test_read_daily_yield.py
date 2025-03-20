#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script di test per verificare la lettura del valore giornaliero dal file JSON
"""

from sense_hat import SenseHat
from classi.inverter_monitor import InverterMonitor
from classi.nighttime_monitor import NighttimeMonitor
import os
import json

def test_read_daily_yield():
    """Test della lettura del valore giornaliero dal file JSON"""
    print("Inizializzazione del test...")
    
    # Inizializza InverterMonitor
    inverter_monitor = InverterMonitor()
    
    # Verifica che il file esista
    print(f"Verifico l'esistenza del file: {inverter_monitor.daily_energy_file}")
    if not os.path.exists(inverter_monitor.daily_energy_file):
        print(f"ERRORE: File {inverter_monitor.daily_energy_file} non trovato!")
        return
    
    # Visualizza il contenuto del file
    try:
        with open(inverter_monitor.daily_energy_file, 'r') as f:
            data = json.load(f)
            print(f"Contenuto del file JSON:")
            for key, value in data.items():
                print(f"  {key}: {value}")
    except Exception as e:
        print(f"ERRORE nella lettura del file: {e}")
        return
    
    # Leggi il valore usando il metodo di InverterMonitor
    value = inverter_monitor.read_daily_power_from_file()
    if value is not None:
        print(f"Valore letto da InverterMonitor.read_daily_power_from_file(): {value} kWh")
    else:
        print("ERRORE: read_daily_power_from_file() ha restituito None")
    
    # Inizializza NighttimeMonitor
    sense = SenseHat()
    nighttime_monitor = NighttimeMonitor(sense, inverter_monitor)
    
    # Verifica il valore memorizzato in NighttimeMonitor
    print(f"Valore in NighttimeMonitor.last_daily_yield: {nighttime_monitor.last_daily_yield} kWh")
    
    # Test della visualizzazione
    print("Test della visualizzazione del valore...")
    nighttime_monitor.display_daily_yield()
    
    print("Test completato.")

if __name__ == "__main__":
    test_read_daily_yield() 