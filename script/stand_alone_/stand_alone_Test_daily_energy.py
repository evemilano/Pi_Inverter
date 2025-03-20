#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pymodbus.client import ModbusTcpClient
import time

# Configurazione dell'inverter
INVERTER_IP = "192.168.1.11"  # indirizzo inverter
MODBUS_PORT = 502             # porta standard Modbus TCP

# Registro per l'energia giornaliera prodotta (in kWh)
DAILY_ENERGY_REGISTER = 32114
DAILY_ENERGY_COUNT = 2  # 32-bit = 2 registri

# Registro per la potenza attiva
POWER_REGISTER = 32324
POWER_COUNT = 2  # 32-bit = 2 registri

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

def main():
    print("Test di lettura dei valori dall'inverter")
    print(f"Inverter IP: {INVERTER_IP}, Porta: {MODBUS_PORT}")
    
    # Leggi la potenza attuale
    power = query_register(POWER_REGISTER, POWER_COUNT, "potenza attuale")
    if power is not None:
        print(f"Potenza attuale: {power} W")
    
    # Leggi l'energia giornaliera
    daily_energy = query_register(DAILY_ENERGY_REGISTER, DAILY_ENERGY_COUNT, "energia giornaliera")
    if daily_energy is not None:
        # Il valore è in kWh con un fattore di scala di 10
        daily_energy_kwh = daily_energy / 10.0
        print(f"Energia giornaliera: {daily_energy_kwh} kWh")
    
    # Leggi l'energia totale
    total_energy = query_register(TOTAL_ENERGY_REGISTER, TOTAL_ENERGY_COUNT, "energia totale")
    if total_energy is not None:
        # Il valore è in kWh con un fattore di scala di 10
        total_energy_kwh = total_energy / 10.0
        print(f"Energia totale: {total_energy_kwh} kWh")

if __name__ == "__main__":
    main() 