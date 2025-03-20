#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pymodbus.client import ModbusTcpClient
import time
from datetime import datetime

# Configurazione dell'inverter
INVERTER_IP = "192.168.1.11"  # indirizzo inverter
MODBUS_PORT = 502             # porta standard Modbus TCP

# Registro per l'energia giornaliera prodotta (in kWh)
DAILY_ENERGY_REGISTER = 32114
DAILY_ENERGY_COUNT = 2  # 32-bit = 2 registri

# Registro per la potenza attiva attuale (in W)
POWER_REGISTER = 32324
POWER_COUNT = 2  # 32-bit = 2 registri

# Registro per l'energia totale prodotta (in kWh)
TOTAL_ENERGY_REGISTER = 32106
TOTAL_ENERGY_COUNT = 2  # 32-bit = 2 registri

# Registro per lo stato dell'inverter
STATUS_REGISTER = 32000
STATUS_COUNT = 2

def query_register(register, count, name, scale_factor=1.0):
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
            
            # Applica il fattore di scala se necessario
            scaled_value = value / scale_factor
            
            print(f"Lettura {name} completata con successo: {scaled_value} (valore raw: {value}, registri: {result.registers})")
            return scaled_value, result.registers

        except Exception as e:
            print(f"Tentativo {attempt}: Errore nella lettura di {name} dall'inverter: {e}")

        finally:
            client.close()

        # Se il tentativo non è andato a buon fine, aspetta prima di riprovare.
        time.sleep(1)

    # Se tutti i tentativi falliscono, restituisci None
    print(f"Tutti i tentativi di lettura di {name} dall'inverter sono falliti.")
    return None, None

def read_multiple_registers(start_register, count):
    """
    Legge un blocco di registri consecutivi dall'inverter.
    """
    print(f"Lettura blocco di registri {start_register}-{start_register+count-1}...")
    
    client = ModbusTcpClient(INVERTER_IP, port=MODBUS_PORT)
    client.unit = 1
    try:
        if not client.connect():
            print("Connessione fallita con l'inverter")
            return None
        
        result = client.read_holding_registers(address=start_register, count=count)
        if result.isError() or not hasattr(result, 'registers'):
            print(f"Errore nella lettura dei registri: {result}")
            return None
        
        return result.registers
    except Exception as e:
        print(f"Errore: {e}")
        return None
    finally:
        client.close()

def main():
    print("Test dettagliato del registro dell'energia giornaliera")
    print(f"Inverter IP: {INVERTER_IP}, Porta: {MODBUS_PORT}")
    print(f"Data e ora attuale: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Leggi lo stato dell'inverter
    status_value, status_registers = query_register(STATUS_REGISTER, STATUS_COUNT, "stato dell'inverter")
    if status_value is not None:
        print(f"Stato dell'inverter: {status_value}")
        print(f"Registri di stato raw: {status_registers}")
    
    # Leggi la potenza attuale
    power_value, power_registers = query_register(POWER_REGISTER, POWER_COUNT, "potenza attuale (W)")
    if power_value is not None:
        print(f"Potenza attuale: {power_value} W")
    
    # Leggi l'energia giornaliera
    daily_energy, daily_registers = query_register(DAILY_ENERGY_REGISTER, DAILY_ENERGY_COUNT, "energia giornaliera", scale_factor=10.0)
    if daily_energy is not None:
        print(f"Energia giornaliera: {daily_energy} kWh")
        print(f"Registri energia giornaliera raw: {daily_registers}")
    
    # Leggi l'energia totale
    total_energy, total_registers = query_register(TOTAL_ENERGY_REGISTER, TOTAL_ENERGY_COUNT, "energia totale", scale_factor=10.0)
    if total_energy is not None:
        print(f"Energia totale: {total_energy} kWh")
    
    # Leggi un blocco più ampio di registri intorno all'energia giornaliera
    print("\nLettura di un blocco di registri intorno all'energia giornaliera...")
    surrounding_registers = read_multiple_registers(32110, 10)
    if surrounding_registers:
        print(f"Registri 32110-32119: {surrounding_registers}")
    
    print("\nAnalisi e conclusioni:")
    if daily_energy == 0.0 and power_value == 0.0:
        print("1. L'inverter non sta producendo energia (è notte)")
        print("2. Il registro dell'energia giornaliera è a 0.0 kWh")
        print("3. Possibili spiegazioni:")
        print("   a) L'inverter resetta il contatore giornaliero a mezzanotte")
        print("   b) L'inverter è in modalità di risparmio energetico e non mantiene alcuni registri")
        print("   c) Il registro dell'energia giornaliera è accessibile solo durante le ore di produzione")
    elif daily_energy > 0.0:
        print(f"1. Il registro dell'energia giornaliera contiene un valore positivo: {daily_energy} kWh")
        print("2. Questo conferma che l'inverter mantiene il valore dell'energia giornaliera anche di notte")
    else:
        print("Risultati non conclusivi. Sono necessari ulteriori test.")
    
    print("\nRaccomandazioni:")
    print("1. Testare nuovamente durante il giorno per verificare che il registro si aggiorni correttamente")
    print("2. Testare a diverse ore della notte per verificare se/quando avviene il reset")
    print("3. Consultare la documentazione Huawei per il modello specifico dell'inverter")

if __name__ == "__main__":
    main() 