#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitor potenza rete — registro Modbus 37113 (i32, gain 1000).
Restituisce la potenza in kW (positivo=consumo, negativo=export).
Zero display, zero CSV.
"""

from ..core.modbus_client import read_register, decode_int32
from .. import config


def read(client):
    """
    Legge il registro potenza rete.

    Args:
        client: ModbusTcpClient attivo

    Returns:
        Potenza rete in kW (float), 0.0 se la lettura fallisce.
    """
    registers = read_register(client, config.GRID_REGISTER, config.REGISTER_COUNT)
    if registers is not None:
        return decode_int32(registers, signed=True) / 1000.0
    return 0.0
