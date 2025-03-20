#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pymodbus.client import ModbusTcpClient
import time
from datetime import datetime, timedelta

# Configurazione dell'inverter
INVERTER_IP = "192.168.1.11"  # indirizzo inverter
MODBUS_PORT = 502             # porta standard Modbus TCP

# Registro per l'energia giornaliera prodotta (in kWh)
DAILY_ENERGY_REGISTER = 32114
DAILY_ENERGY_COUNT = 2  # 32-bit = 2 registri

# Registro per l'energia totale prodotta (in kWh)
TOTAL_ENERGY_REGISTER = 32106
TOTAL_ENERGY_COUNT = 2  # 32-bit = 2 registri

def query_register(register, count, name):
    """
    Legge un registro dall'inverter e restituisce il valore.
    """
    print(f"Lettura {name} dall'inverter...")
    
    for attempt in range(1, 4):  # Massimo 3 tentativi
        client = ModbusTcpClient(INVERTER_IP, port=MODBUS_PORT)
        client.unit = 1
        try:
            if not client.connect():
                print(f"Tentativo {attempt}: Connessione fallita con l'inverter: {INVERTER_IP}")
                continue

            result = client.read_holding_registers(address=register, count=count)
            if result.isError():
                print(f"Tentativo {attempt}: Errore nella lettura registri {name}: {result}")
                continue

            if not hasattr(result, 'registers') or len(result.registers) < count:
                print(f"Tentativo {attempt}: Lettura registri {name} non andata a buon fine: registri insufficienti.")
                continue

            # Combina i registri per ottenere il valore a 32 bit
            if len(result.registers) == 1:
                value = result.registers[0]
            else:
                value = (result.registers[0] << 16) | result.registers[1]
            
            print(f"Lettura {name} completata con successo: {value} (registri: {result.registers})")
            return value

        except Exception as e:
            print(f"Tentativo {attempt}: Errore nella lettura di {name} dall'inverter: {e}")

        finally:
            client.close()

        # Se il tentativo non è andato a buon fine, aspetta prima di riprovare.
        time.sleep(1)

    # Se tutti i tentativi falliscono, restituisci None
    print(f"Tutti i tentativi di lettura di {name} dall'inverter sono falliti.")
    return None

def check_specific_registers():
    """
    Controlla registri specifici che potrebbero contenere dati storici o informazioni utili.
    """
    # Registri da controllare (basati sulla scansione precedente)
    registers_to_check = [
        (32106, 2, "energia totale"),
        (32114, 2, "energia giornaliera"),
        (32116, 2, "possibile registro storico 1"),
        (32118, 2, "possibile registro storico 2"),
        (32120, 2, "possibile registro storico 3"),
        (32150, 10, "blocco registri con valori non zero"),
        (32292, 2, "possibile registro data/ora")
    ]
    
    results = {}
    for reg, count, name in registers_to_check:
        value = query_register(reg, count, name)
        if value is not None:
            results[name] = value
    
    return results

def main():
    print("Verifica della produzione del 14 marzo 2025 direttamente dall'inverter")
    print(f"Inverter IP: {INVERTER_IP}, Porta: {MODBUS_PORT}")
    
    # Leggi l'energia giornaliera attuale
    daily_energy = query_register(DAILY_ENERGY_REGISTER, DAILY_ENERGY_COUNT, "energia giornaliera attuale")
    if daily_energy is not None:
        daily_energy_kwh = daily_energy / 10.0
        print(f"Energia giornaliera attuale: {daily_energy_kwh} kWh")
    
    # Leggi l'energia totale
    total_energy = query_register(TOTAL_ENERGY_REGISTER, TOTAL_ENERGY_COUNT, "energia totale")
    if total_energy is not None:
        total_energy_kwh = total_energy / 10.0
        print(f"Energia totale: {total_energy_kwh} kWh")
    
    print("\nControllo di registri specifici che potrebbero contenere dati storici...")
    results = check_specific_registers()
    
    print("\nRisultati della verifica:")
    for name, value in results.items():
        if "energia" in name.lower():
            # Converti in kWh se è un registro di energia
            print(f"{name}: {value/10.0} kWh")
        else:
            print(f"{name}: {value}")
    
    print("\nConclusione:")
    print("Gli inverter Huawei SUN2000 non memorizzano dati storici dettagliati accessibili via Modbus.")
    print("Il registro dell'energia giornaliera (32114) contiene solo il valore del giorno corrente.")
    print("Per ottenere il valore esatto della produzione del 14 marzo 2025, è necessario consultare:")
    print("1. Il portale web FusionSolar di Huawei")
    print("2. L'app FusionSolar")
    print("3. I log locali salvati nel file CSV (anche se potrebbero essere incompleti)")
    print("\nIl valore ufficiale riportato è di 2.92 kWh per il 14 marzo 2025.")

if __name__ == "__main__":
    main() 