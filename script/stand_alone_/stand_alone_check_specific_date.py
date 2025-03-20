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

# Registro per la potenza attiva
POWER_REGISTER = 32324
POWER_COUNT = 2  # 32-bit = 2 registri

# Registro per l'energia totale prodotta (in kWh)
TOTAL_ENERGY_REGISTER = 32106
TOTAL_ENERGY_COUNT = 2  # 32-bit = 2 registri

# Registri per i dati storici (se disponibili)
# Nota: questi registri potrebbero non essere disponibili o potrebbero variare in base al modello dell'inverter
HISTORICAL_DATA_START_REGISTER = 33000  # Esempio, da verificare nella documentazione dell'inverter
HISTORICAL_DATA_COUNT = 2

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

def scan_registers_for_historical_data():
    """
    Scansiona un intervallo di registri per cercare dati storici.
    Questa è una funzione esplorativa per trovare registri che potrebbero contenere dati storici.
    """
    print("Scansione dei registri per cercare dati storici...")
    
    # Intervallo di registri da scansionare
    start_register = 32000
    end_register = 33000
    step = 10  # Leggi 10 registri alla volta
    
    for register in range(start_register, end_register, step):
        try:
            client = ModbusTcpClient(INVERTER_IP, port=MODBUS_PORT)
            client.unit = 1
            if client.connect():
                result = client.read_holding_registers(address=register, count=step)
                if not result.isError() and hasattr(result, 'registers'):
                    non_zero_values = [i for i, val in enumerate(result.registers) if val != 0]
                    if non_zero_values:
                        print(f"Registri {register}-{register+step-1}: {result.registers}")
                        print(f"Valori non zero trovati agli indici: {non_zero_values}")
            client.close()
        except Exception as e:
            print(f"Errore nella scansione del registro {register}: {e}")
        
        time.sleep(0.5)  # Pausa tra le letture per non sovraccaricare l'inverter

def query_historical_data(target_date_str="2025-03-14"):
    """
    Tenta di leggere i dati storici per una data specifica.
    Nota: questa funzione è sperimentale e potrebbe non funzionare con tutti gli inverter.
    """
    print(f"Tentativo di lettura dei dati storici per {target_date_str}...")
    
    # Converti la data target in un formato che l'inverter potrebbe utilizzare
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
    days_since_epoch = (target_date - datetime(1970, 1, 1)).days
    
    print(f"Giorni dall'epoca: {days_since_epoch}")
    
    # Prova a leggere i dati storici usando diversi approcci
    # Questo è sperimentale e potrebbe richiedere adattamenti in base al modello dell'inverter
    
    # Approccio 1: Prova a leggere un registro che potrebbe contenere un indice per i dati storici
    index_register = query_register(33000, 1, "indice dati storici")
    if index_register is not None:
        print(f"Indice dati storici: {index_register}")
    
    # Approccio 2: Prova a leggere direttamente i dati per la data target
    # Questo è molto sperimentale e richiede conoscenza del formato dei dati dell'inverter
    data_register = query_register(33001 + days_since_epoch % 365, 2, f"dati per {target_date_str}")
    if data_register is not None:
        print(f"Dati per {target_date_str}: {data_register}")
    
    return None  # Questa funzione è principalmente esplorativa

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
    
    print("\nNota: La maggior parte degli inverter non memorizza dati storici dettagliati accessibili via Modbus.")
    print("Per ottenere dati storici specifici, è necessario utilizzare il portale web del produttore o l'app dedicata.")
    
    # Chiedi all'utente se vuole eseguire una scansione esplorativa
    response = input("\nVuoi eseguire una scansione esplorativa dei registri? (s/n): ")
    if response.lower() == 's':
        scan_registers_for_historical_data()
    
    # Tenta comunque di leggere i dati storici (funzione sperimentale)
    query_historical_data("2025-03-14")
    
    print("\nPer ottenere il valore esatto della produzione del 14 marzo 2025, controlla:")
    print("1. Il portale web del produttore dell'inverter")
    print("2. L'app dedicata per il monitoraggio dell'impianto")
    print("3. Il display dell'inverter stesso (se disponibile)")
    print("4. I log locali salvati nel file CSV (anche se potrebbero essere incompleti)")

if __name__ == "__main__":
    main() 