#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script standalone per leggere tutti i registri disponibili dall'inverter Huawei SUN2000.
Il file è indipendente e non richiede altre classi per funzionare.

Esegui lo script con il venv:
/home/pi/Python/script/Pi_Inverter/venv/bin/python /home/pi/Python/script/Pi_Inverter/stand_alone_/all_registers.py
"""

import time
import json
from pymodbus.client import ModbusTcpClient
from datetime import datetime

# Configurazione dell'inverter
INVERTER_IP = "192.168.1.11"  # Indirizzo IP dell'inverter
MODBUS_PORT = 502             # Porta Modbus TCP standard
MAX_RETRIES = 3               # Numero massimo di tentativi di connessione

# Definizione dei registri da leggere
REGISTERS = [
    # 3.1 Inverter Equipment Register
    {"name": "Model", "address": 30000, "count": 15, "type": "string"},
    {"name": "SN", "address": 30015, "count": 10, "type": "string"},
    {"name": "PN", "address": 30025, "count": 10, "type": "string"},
    {"name": "Model ID", "address": 30070, "count": 1, "type": "u16"},
    {"name": "Number of PV strings", "address": 30071, "count": 1, "type": "u16"},
    {"name": "Number of MPP trackers", "address": 30072, "count": 1, "type": "u16"},
    {"name": "Rated power (Pn)", "address": 30073, "count": 2, "type": "u32", "gain": 1000},
    {"name": "Maximum active power (Pmax)", "address": 30075, "count": 2, "type": "u32", "gain": 1000},
    {"name": "Maximum apparent power (Smax)", "address": 30077, "count": 2, "type": "u32", "gain": 1000},
    {"name": "Maximum reactive power (Qmax)", "address": 30079, "count": 2, "type": "i32", "gain": 1000},
    {"name": "CPLD version", "address": 31040, "count": 1, "type": "u16"},
    {"name": "AFCI version", "address": 31070, "count": 1, "type": "u16"},
    {"name": "DC-MBUS version", "address": 31085, "count": 1, "type": "u16"},
    {"name": "REGKEY", "address": 31115, "count": 1, "type": "u16"},
    {"name": "Single-machine remote communication", "address": 31200, "count": 1, "type": "u16"},
    {"name": "Alarm 3", "address": 32000, "count": 2, "type": "u32"},
    {"name": "ESN", "address": 32010, "count": 2, "type": "u32"},
    
    # PV inputs
    {"name": "PV1 voltage", "address": 32015, "count": 1, "type": "i16", "gain": 10, "unit": "V"},
    {"name": "PV1 current", "address": 32016, "count": 1, "type": "i16", "gain": 100, "unit": "A"},
    
    # Aggregati
    {"name": "Input power", "address": 32064, "count": 2, "type": "i32", "gain": 1000, "unit": "kW"},
    {"name": "DC input voltage", "address": 32066, "count": 1, "type": "i16", "gain": 10, "unit": "V"},
    {"name": "DC input current", "address": 32068, "count": 1, "type": "i16", "gain": 100, "unit": "A"},
    {"name": "String input current", "address": 32070, "count": 1, "type": "i16", "gain": 100, "unit": "A"},
    
    # Grid metrics
    {"name": "Grid voltage (A phase)", "address": 32072, "count": 1, "type": "i16", "gain": 10, "unit": "V"},
    {"name": "B phase voltage", "address": 32074, "count": 1, "type": "i16", "gain": 10, "unit": "V"},
    {"name": "C phase voltage", "address": 32076, "count": 1, "type": "i16", "gain": 10, "unit": "V"},
    {"name": "Grid frequency", "address": 32078, "count": 1, "type": "i16", "gain": 100, "unit": "Hz"},
    {"name": "Active power", "address": 32080, "count": 2, "type": "i32", "gain": 1000, "unit": "kW"},
    {"name": "Reactive power", "address": 32082, "count": 2, "type": "i32", "gain": 1000, "unit": "kVar"},
    {"name": "Power factor", "address": 32084, "count": 1, "type": "i16", "gain": 1000},
    {"name": "Grid frequency (2)", "address": 32085, "count": 1, "type": "i16", "gain": 100, "unit": "Hz"},
    {"name": "Efficiency", "address": 32086, "count": 1, "type": "i16", "gain": 100, "unit": "%"},
    {"name": "Internal temperature", "address": 32087, "count": 1, "type": "i16", "gain": 10, "unit": "°C"},
    {"name": "Daily energy yield", "address": 32114, "count": 2, "type": "u32", "gain": 100, "unit": "kWh"},
    
    # Management and features
    {"name": "Management system status", "address": 35127, "count": 1, "type": "u16"},
    {"name": "Smart I-V Curve Diagnosis Authorization", "address": 35136, "count": 1, "type": "u16"},
    {"name": "Smart I-V Curve Diagnosis License status", "address": 35138, "count": 1, "type": "u16"},
    {"name": "Smart I-V Curve Diagnosis License expiration", "address": 35139, "count": 2, "type": "u32"},
    {"name": "License loading time", "address": 35141, "count": 2, "type": "u32"},
    {"name": "License revocation time", "address": 35143, "count": 2, "type": "u32"},
    {"name": "License SN", "address": 35145, "count": 10, "type": "string"},
    {"name": "Revocation code", "address": 35155, "count": 5, "type": "string"},
    
    # 4G Module
    {"name": "4G Module status", "address": 35249, "count": 1, "type": "u16"},
    {"name": "4G IP address", "address": 35250, "count": 2, "type": "u32"},
    {"name": "4G Subnet mask", "address": 35252, "count": 2, "type": "u32"},
    {"name": "4G IMEI", "address": 35254, "count": 10, "type": "string"},
    {"name": "4G Signal strength", "address": 35264, "count": 1, "type": "u16"},
    {"name": "4G Maximum number of PIN attempts", "address": 35265, "count": 1, "type": "u16"},
    {"name": "4G PIN verification status", "address": 35266, "count": 1, "type": "u16"},
    {"name": "Original model name", "address": 35268, "count": 15, "type": "string"},
    
    # Power Adjustment
    {"name": "Active Adjustment mode", "address": 35300, "count": 1, "type": "u16"},
    {"name": "Reactive Adjustment mode", "address": 35304, "count": 1, "type": "u16"},
    
    # Optimizer
    {"name": "Total number of optimizers", "address": 37200, "count": 1, "type": "u16"},
    {"name": "Number of online optimizers", "address": 37201, "count": 1, "type": "u16"},
    {"name": "Optimizer Feature data", "address": 37202, "count": 1, "type": "u16"},
    
    # System settings
    {"name": "System time", "address": 40000, "count": 2, "type": "u32"},
    {"name": "Default maximum feed-in power", "address": 47675, "count": 2, "type": "u32", "gain": 1000, "unit": "kW"},
    {"name": "Default active power change gradient", "address": 47677, "count": 1, "type": "u16", "gain": 10, "unit": "%/s"},
    
    # Meter registers (3.3)
    {"name": "Meter status", "address": 37100, "count": 1, "type": "u16"},
    {"name": "Meter Grid voltage (A phase)", "address": 37101, "count": 2, "type": "i32", "gain": 10, "unit": "V"},
    {"name": "Meter B phase voltage", "address": 37103, "count": 2, "type": "i32", "gain": 10, "unit": "V"},
    {"name": "Meter C phase voltage", "address": 37105, "count": 2, "type": "i32", "gain": 10, "unit": "V"},
    {"name": "Meter Grid current (A phase)", "address": 37107, "count": 2, "type": "i32", "gain": 100, "unit": "A"},
    {"name": "Meter B phase current", "address": 37109, "count": 2, "type": "i32", "gain": 100, "unit": "A"},
    {"name": "Meter C phase current", "address": 37111, "count": 2, "type": "i32", "gain": 100, "unit": "A"},
    {"name": "Meter Active power", "address": 37113, "count": 2, "type": "i32", "gain": 1000, "unit": "kW"},
    {"name": "Meter Reactive power", "address": 37115, "count": 2, "type": "i32", "gain": 1000, "unit": "kVar"},
    {"name": "Meter Apparent power", "address": 37117, "count": 2, "type": "i32", "gain": 1000, "unit": "kVA"},
    {"name": "Meter Power factor", "address": 37119, "count": 2, "type": "i32", "gain": 1000},
    
    # Battery registers (solo alcuni principali da 3.2)
    {"name": "Energy storage unit 1 Running status", "address": 37000, "count": 1, "type": "u16"},
    {"name": "Energy storage unit 1 Charge and discharge power", "address": 37001, "count": 2, "type": "i32", "gain": 1, "unit": "W"},
    {"name": "Energy storage unit 1 Battery SOC", "address": 37004, "count": 2, "type": "u32", "gain": 10, "unit": "%"},
    {"name": "Energy storage unit 1 Working mode", "address": 37006, "count": 1, "type": "u16"}
]

def decode_value(registers, reg_def):
    """
    Decodifica i registri letti in base al tipo di dato specificato
    
    Args:
        registers (list): Lista di registri letti
        reg_def (dict): Definizione del registro con tipo e gain
        
    Returns:
        Valore decodificato in base al tipo
    """
    reg_type = reg_def.get("type", "u16")
    gain = reg_def.get("gain", 1)
    
    if reg_type == "string":
        # Decodifica stringa - ogni registro contiene 2 caratteri ASCII
        chars = []
        for reg in registers:
            chars.append(chr((reg >> 8) & 0xFF))
            chars.append(chr(reg & 0xFF))
        return ''.join(c for c in chars if ord(c) > 0)
    
    elif reg_type == "u16":
        return registers[0]
    
    elif reg_type == "i16":
        value = registers[0]
        if value & 0x8000:  # Test if sign bit is set
            value = -((~value & 0xFFFF) + 1)
        return value / gain if gain > 1 else value
    
    elif reg_type == "u32":
        if len(registers) < 2:
            return None
        return ((registers[0] << 16) | registers[1]) / gain if gain > 1 else ((registers[0] << 16) | registers[1])
    
    elif reg_type == "i32":
        if len(registers) < 2:
            return None
        value = (registers[0] << 16) | registers[1]
        if value & 0x80000000:  # Test if sign bit is set
            value = -((~value & 0xFFFFFFFF) + 1)
        return value / gain if gain > 1 else value
    
    return None

def read_registers(client, address, count):
    """
    Legge un blocco di registri dall'inverter
    
    Args:
        client: Client Modbus connesso
        address: Indirizzo del primo registro da leggere
        count: Numero di registri da leggere
        
    Returns:
        Lista di registri letti o None in caso di errore
    """
    try:
        result = client.read_holding_registers(address=address, count=count)
        if result.isError():
            return None
        
        if not hasattr(result, 'registers') or len(result.registers) < count:
            return None
            
        return result.registers
    except Exception as e:
        print(f"Errore nella lettura dei registri all'indirizzo {address}: {e}")
        return None

def read_register_with_retry(register_def, max_retries=3, delay=1):
    """
    Legge un registro con tentativi multipli in caso di errore
    
    Args:
        register_def: Definizione del registro da leggere
        max_retries: Numero massimo di tentativi
        delay: Ritardo tra i tentativi in secondi
        
    Returns:
        Valore decodificato del registro o None in caso di errore
    """
    address = register_def["address"]
    count = register_def["count"]
    name = register_def["name"]
    
    for attempt in range(1, max_retries + 1):
        client = ModbusTcpClient(INVERTER_IP, port=MODBUS_PORT)
        client.unit = 1  # Unit ID (slave)
        
        try:
            if not client.connect():
                print(f"Tentativo {attempt}: Connessione fallita")
                continue
                
            registers = read_registers(client, address, count)
            if registers:
                value = decode_value(registers, register_def)
                unit = register_def.get("unit", "")
                if unit:
                    return f"{value} {unit}"
                return value
        
        except Exception as e:
            print(f"Tentativo {attempt}: Errore nella lettura del registro {name}: {e}")
        
        finally:
            client.close()
            
        if attempt < max_retries:
            time.sleep(delay)
    
    return None

def read_all_registers():
    """
    Legge tutti i registri definiti e restituisce un dizionario con i risultati
    
    Returns:
        Dizionario con i valori letti da ogni registro
    """
    results = {}
    total = len(REGISTERS)
    
    for i, reg in enumerate(REGISTERS, 1):
        name = reg["name"]
        print(f"Lettura registro {i}/{total}: {name} (indirizzo: {reg['address']})...")
        
        value = read_register_with_retry(reg)
        results[name] = value
        
        # Piccola pausa tra le letture per non sovraccaricare l'inverter
        time.sleep(0.2)
    
    return results

def main():
    """Funzione principale che legge tutti i registri dell'inverter"""
    print("-" * 70)
    print(f"Lettura di tutti i registri dall'inverter Huawei SUN2000: {datetime.now()}")
    print("-" * 70)
    
    # Leggi tutti i registri
    results = read_all_registers()
    
    # Stampa i risultati in un formato leggibile
    print("\nRISULTATI:")
    print("-" * 70)
    for name, value in results.items():
        if value is not None:
            print(f"{name:40}: {value}")
        else:
            print(f"{name:40}: Non disponibile")
    
    # Salva i risultati in un file JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"inverter_registers_{timestamp}.json"
    filepath = f"/home/pi/Python/script/Pi_Inverter/stand_alone_/{filename}"
    
    with open(filepath, 'w') as f:
        json.dump({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "inverter_ip": INVERTER_IP,
            "registers": results
        }, f, indent=4)
    
    print("-" * 70)
    print(f"I risultati sono stati salvati nel file: {filepath}")
    print("-" * 70)

if __name__ == "__main__":
    main() 