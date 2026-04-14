#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitor produzione giornaliera — registro Modbus 32114 (u32, gain 100).
Restituisce il valore in kWh. Aggiorna solo una volta per ora (guard).
Zero display, zero CSV diretto.
"""

from datetime import datetime

from ..core.modbus_client import read_register, decode_int32
from ..core import data_store
from .. import config


_last_updated_hour = None


def read(client):
    """
    Legge il registro produzione giornaliera.

    Args:
        client: ModbusTcpClient attivo

    Returns:
        Produzione giornaliera in kWh (float), None se la lettura fallisce.
    """
    registers = read_register(client, config.DAILY_YIELD_REGISTER, config.REGISTER_COUNT)
    if registers is not None:
        return decode_int32(registers, signed=False) / 100.0
    return None


def update_if_needed(client):
    """
    Aggiorna il daily yield solo se nelle ore giuste e non gia aggiornato
    in questa ora. Persiste il valore su JSON.

    Args:
        client: ModbusTcpClient attivo

    Returns:
        True se un nuovo valore e stato salvato, False altrimenti.
    """
    global _last_updated_hour

    current_hour = datetime.now().hour

    if current_hour not in config.DAILY_YIELD_HOURS:
        return False

    if current_hour == _last_updated_hour:
        return False

    value = read(client)
    if value is not None and data_store.save_daily_energy(config.DAILY_ENERGY_JSON, value):
        _last_updated_hour = current_hour
        print(f"Daily yield aggiornato alle {current_hour}:00: {value} kWh")
        return True

    return False


def get_last_daily_yield():
    """
    Legge l'ultimo daily yield salvato sul JSON.

    Returns:
        Valore in kWh (float), 0.0 se il file non esiste o e vuoto.
    """
    value = data_store.read_daily_energy(config.DAILY_ENERGY_JSON)
    return value if value is not None else 0.0
