#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script di test per leggere i dati di energia giornaliera dall'inverter Huawei SUN2000
"""

import time
from pymodbus.client import ModbusTcpClient
from datetime import datetime

# Configurazione dell'inverter
INVERTER_IP = "192.168.1.11"  # Indirizzo IP dell'inverter
MODBUS_PORT = 502             # Porta Modbus TCP standard
MAX_RETRIES = 3               # Numero massimo di tentativi di connessione

# Registri Modbus importanti trovati nella documentazione
POWER_REGISTER = 32324        # Potenza attiva istantanea
DAILY_YIELD_REGISTER = 32114  # Produzione giornaliera in kWh
TOTAL_YIELD_REGISTER = 32106  # Produzione totale in kWh

# Funzione principale per leggere i registri Modbus dall'inverter
def read_inverter_register(register, count=2):
    """
    Legge un registro dall'inverter con gestione degli errori e riprova.
    
    Args:
        register: Numero del registro Modbus da leggere
        count: Numero di registri da leggere (default 2 per valori a 32 bit)
        
    Returns:
        Il valore letto dal registro o None in caso di errore
    """
    for attempt in range(1, MAX_RETRIES + 1):
        client = ModbusTcpClient(INVERTER_IP, port=MODBUS_PORT)
        client.unit = 1  # Unit ID (slave)

        try:
            print(f"Tentativo {attempt}: Connessione all'inverter: {INVERTER_IP}")
            if not client.connect():
                print(f"Tentativo {attempt}: Connessione fallita")
                continue

            result = client.read_holding_registers(address=register, count=count)
            if result.isError():
                print(f"Tentativo {attempt}: Errore nella lettura registri: {result}")
                continue

            if not hasattr(result, 'registers') or len(result.registers) < count:
                print(f"Tentativo {attempt}: Lettura registri insufficienti")
                continue

            # Se leggiamo un solo registro, restituisci direttamente il valore
            if count == 1:
                return result.registers[0]
            # Per valori a 32 bit, combina i due registri
            elif count == 2:
                value = (result.registers[0] << 16) | result.registers[1]
                return value

        except Exception as e:
            print(f"Tentativo {attempt}: Errore nella lettura dall'inverter: {e}")

        finally:
            client.close()

        # Attendi prima di riprovare
        if attempt < MAX_RETRIES:
            time.sleep(1)

    print("Tutti i tentativi di lettura dall'inverter sono falliti.")
    return None

def main():
    """Funzione principale che legge diversi registri dall'inverter"""
    print("-" * 50)
    print(f"Test di lettura dall'inverter Huawei SUN2000: {datetime.now()}")
    print("-" * 50)
    
    # Leggi la potenza attiva istantanea (W)
    power = read_inverter_register(POWER_REGISTER)
    if power is not None:
        print(f"Potenza attiva istantanea: {power} W")
    
    # Leggi la produzione giornaliera (kWh)
    daily_yield = read_inverter_register(DAILY_YIELD_REGISTER)
    if daily_yield is not None:
        # Il valore deve essere diviso per 100 per ottenere i kWh secondo la doc
        daily_yield_kwh = daily_yield / 100.0
        print(f"Produzione giornaliera: {daily_yield_kwh:.2f} kWh")
    
    # Leggi la produzione totale (kWh)
    total_yield = read_inverter_register(TOTAL_YIELD_REGISTER)
    if total_yield is not None:
        # Il valore deve essere diviso per 100 per ottenere i kWh secondo la doc
        total_yield_kwh = total_yield / 100.0
        print(f"Produzione totale: {total_yield_kwh:.2f} kWh")
    
    print("-" * 50)

if __name__ == "__main__":
    main() 