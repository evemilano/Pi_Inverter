#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitor potenza solare — registro Modbus 32080 (i32, gain 1000).
Restituisce la potenza in watt. Zero display, zero CSV.
"""

from ..core.modbus_client import read_register, decode_int32
from .. import config


def read(client):
    """
    Legge il registro potenza solare.

    Args:
        client: ModbusTcpClient attivo

    Returns:
        Potenza solare in watt (int), 0 se la lettura fallisce.
    """
    registers = read_register(client, config.SOLAR_REGISTER, config.REGISTER_COUNT)
    if registers is not None:
        return decode_int32(registers, signed=True)
    return 0
