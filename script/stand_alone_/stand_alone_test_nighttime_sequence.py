#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script di test per verificare la sequenza di visualizzazione notturna
"""

import time
from sense_hat import SenseHat
from classi.inverter_monitor import InverterMonitor
from classi.nighttime_monitor import NighttimeMonitor

def test_nighttime_sequence():
    """Test della sequenza di visualizzazione notturna"""
    print("Inizializzazione del test...")
    
    # Inizializza i componenti
    inverter_monitor = InverterMonitor()
    nighttime_monitor = NighttimeMonitor(inverter_monitor.sense, inverter_monitor)
    
    print("Test della sequenza di visualizzazione notturna...")
    print("Mostrando: grafico -> breve pausa -> testo -> grafico")
    
    # Esegui update() per vedere la sequenza completa
    # Questo mostrerà:
    # 1. Il grafico
    # 2. Una breve pausa di 1 secondo
    # 3. Il testo "Daily power" due volte
    # 4. Il grafico di nuovo
    nighttime_monitor.update()
    
    print("Test completato. Verifica che il display abbia mostrato:")
    print("1. Il grafico delle potenze del giorno")
    print("2. Il testo 'Daily power: X.XX kWh' due volte")
    print("3. Il grafico di nuovo")
    print("Il tutto senza lunghe pause a schermo nero")

if __name__ == "__main__":
    test_nighttime_sequence() 