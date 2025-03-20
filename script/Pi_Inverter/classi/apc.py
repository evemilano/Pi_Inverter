#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script standalone per leggere i dati dal registro specifico dell'inverter Huawei SUN2000.
Il file è indipendente e non richiede altre classi per funzionare.

Query specifica per il registro 30081 dell'inverter, che rappresenta:
    Maximum reactive power (Qmax, absorbed from the power grid)
Accesso: RO, Tipo di dato: I32, Unità: kVar, Guadagno: 1000, Quantità: 2 registri.
Utilizza la funzione Modbus 0x03 (Read registers).
"""

import time
from pymodbus.client import ModbusTcpClient
from datetime import datetime

# Configurazione dell'inverter
INVERTER_IP = "192.168.1.11"  # Indirizzo IP dell'inverter
MODBUS_PORT = 502             # Porta Modbus TCP standard
TARGET_REGISTER = 37113       # Indirizzo decimale del registro

def decode_int32_signed(registers):
    """
    Decodifica due registri a 16 bit in un valore intero signed a 32 bit.
    
    Args:
        registers (list): Lista di due registri a 16 bit.
        
    Returns:
        int: Valore intero signed a 32 bit.
    """
    value = (registers[0] << 16) | registers[1]
    # Controlla se il bit più significativo è 1 (numero negativo in complemento a 2)
    if value & 0x80000000:
        value = -((~value & 0xFFFFFFFF) + 1)
    return value

def read_inverter_register(register, count):
    """
    Legge un registro dall'inverter con gestione degli errori e riprova.
    """
    for _ in range(3):
        client = ModbusTcpClient(INVERTER_IP, port=MODBUS_PORT)
        client.unit = 1  # Unit ID (slave)

        try:
            if client.connect():
                result = client.read_holding_registers(address=register, count=count)
                
                if not result.isError() and hasattr(result, 'registers') and len(result.registers) >= count:
                    return result.registers

        except Exception:
            pass

        finally:
            client.close()

        time.sleep(1)

    return None

def main():
    registers = read_inverter_register(TARGET_REGISTER, 2)
    if registers:
        value = decode_int32_signed(registers) / 1000.0
        print(f"{value:.2f}kW")

if __name__ == "__main__":
    main()
