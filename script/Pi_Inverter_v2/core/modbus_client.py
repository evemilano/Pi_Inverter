#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Client Modbus TCP unificato per l'inverter Huawei SUN2000.
Gestisce connessione, lettura registri, decodifica e retry.
"""

import time

from pymodbus.client import ModbusTcpClient

from .. import config


def decode_int32(registers, signed=True):
    """
    Decodifica due registri 16-bit (big-endian) in un intero 32-bit.

    Args:
        registers: lista/tupla di 2 registri 16-bit
        signed: True per interpretare come int32 signed (two's complement)

    Returns:
        Valore intero decodificato.
    """
    value = (registers[0] << 16) | registers[1]
    if signed and (value & 0x80000000):
        value = -((~value & 0xFFFFFFFF) + 1)
    return value


def read_register(client, address, count=2, max_retries=3, delay=1):
    """
    Legge un registro Modbus con retry automatico.

    Args:
        client: ModbusTcpClient gia connesso
        address: indirizzo del registro
        count: numero di word 16-bit da leggere (default 2)
        max_retries: tentativi massimi
        delay: secondi di attesa tra i tentativi

    Returns:
        Lista di registri letti, oppure None se tutti i tentativi falliscono.
    """
    for attempt in range(1, max_retries + 1):
        try:
            result = client.read_holding_registers(address, count=count)
            if not result.isError() and hasattr(result, 'registers') and len(result.registers) >= count:
                return result.registers
        except Exception as e:
            print(f"Tentativo {attempt}/{max_retries}: Errore lettura registro {address}: {e}")

        if attempt < max_retries:
            time.sleep(delay)
    return None


class ModbusSession:
    """
    Context manager per una sessione Modbus TCP.
    Apre una connessione, permette letture multiple, chiude all'uscita.

    Uso:
        with ModbusSession() as client:
            regs = read_register(client, 32080)
    """

    def __init__(self, ip=None, port=None, timeout=None):
        self.ip = ip or config.INVERTER_IP
        self.port = port or config.MODBUS_PORT
        self.timeout = timeout or config.MODBUS_TIMEOUT
        self.client = None

    def __enter__(self):
        self.client = ModbusTcpClient(self.ip, self.port, timeout=self.timeout)
        self.client.unit = config.MODBUS_UNIT_ID
        if not self.client.connect():
            raise ConnectionError(f"Connessione Modbus fallita: {self.ip}:{self.port}")
        return self.client

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            self.client.close()
        return False
