#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pymodbus.client import ModbusTcpClient
import time

class APCMonitor:
    def __init__(self):
        self.INVERTER_IP = "192.168.1.11"
        self.MODBUS_PORT = 502
        self.TARGET_REGISTER = 37113

    def decode_int32_signed(self, registers):
        """
        Decodifica due registri a 16 bit in un valore intero signed a 32 bit.
        
        Args:
            registers (list): Lista di due registri a 16 bit.
            
        Returns:
            int: Valore intero signed a 32 bit.
        """
        value = (registers[0] << 16) | registers[1]
        if value & 0x80000000:
            value = -((~value & 0xFFFFFFFF) + 1)
        return value

    def read_inverter_register(self, register, count, client=None):
        """
        Legge un registro dall'inverter con gestione degli errori e riprova.
        Args:
            register: Indirizzo del registro Modbus
            count: Numero di registri da leggere
            client: Client Modbus già connesso (opzionale). Se fornito, non viene chiuso.
        """
        external_client = client is not None
        for _ in range(3):
            if not external_client:
                client = ModbusTcpClient(self.INVERTER_IP, port=self.MODBUS_PORT, timeout=5)
                client.unit = 1

            try:
                if external_client or client.connect():
                    result = client.read_holding_registers(address=register, count=count)
                    if not result.isError() and hasattr(result, 'registers') and len(result.registers) >= count:
                        return result.registers
            except Exception:
                pass
            finally:
                if not external_client:
                    client.close()
            time.sleep(1)
        return None

    def get_power_consumption(self, client=None):
        """
        Legge il consumo di potenza dalla rete.
        Args:
            client: Client Modbus già connesso (opzionale).
        Returns:
            float: Valore di potenza in kW, 0 se non disponibile
        """
        registers = self.read_inverter_register(self.TARGET_REGISTER, 2, client=client)
        if registers:
            value = self.decode_int32_signed(registers) / 1000.0
            return value
        return 0.0