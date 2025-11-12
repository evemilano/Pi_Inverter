#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from datetime import datetime
from pymodbus.client import ModbusTcpClient
from sense_hat import SenseHat
import time
import json

class InverterMonitor:
    def __init__(self):
        self.sense = SenseHat()
        self.sense.set_rotation(180)
        
        # Costanti
        self.INVERTER_IP = "192.168.1.11"
        self.MODBUS_PORT = 502
        self.POLL_INTERVAL = 60 #60
        self.csv_filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "power_log.csv")
        self.daily_energy_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "last_daily_energy.json")
        self.SERVICE_FILE_PATH = "/etc/systemd/system/rbp4_8gb_inverter.service"
        self.SERVICE_NAME = "rbp4_8gb_inverter.service"
        self.PYTHON_EXEC = sys.executable
        
        # Orari per monitoraggio notturno/diurno
        self.DAY_START_HOUR = 6    # ora di inizio del periodo diurno
        self.DAY_END_HOUR = 20     # ora di fine del periodo diurno
        
        # Registri Modbus
        self.POWER_REGISTER = 32080
        self.DAILY_YIELD_REGISTER = 32114  # Registro per la produzione giornaliera
        self.REGISTER_COUNT = 2
        
        # Colori LED
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.BLACK = (0, 0, 0)
        
        # Inizializza i percorsi
        self.SCRIPT_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "rbp4_8gb_inverter.py"))
        
        # Valori per il daily yield
        self.last_daily_yield = 0.0
        self.last_daily_yield_time = 0

    def decode_int32_signed(self, registers):
        """
        Decodifica due registri a 16 bit in un valore intero signed a 32 bit.
        
        Args:
            registers (list): Lista di due registri a 16 bit
            
        Returns:
            int: Valore intero signed a 32 bit
        """
        value = (registers[0] << 16) | registers[1]
        # Controllo se il bit più significativo è 1 (numero negativo in complemento a 2)
        if value & 0x80000000:
            # Converti da complemento a 2 a signed
            value = -((~value & 0xFFFFFFFF) + 1)
        return value

    def query_inverter(self, max_retries=3, delay=1):
        """Tenta di leggere il valore dell'inverter fino a max_retries volte."""
        for attempt in range(1, max_retries + 1):
            client = ModbusTcpClient(self.INVERTER_IP, port=self.MODBUS_PORT)
            client.unit = 1
            try:
                if not client.connect():
                    self.sense.show_message(f"Tentativo {attempt}: Connessione fallita con l'inverter: {self.INVERTER_IP}", 
                                         text_colour=self.RED, scroll_speed=0.03)
                    continue

                result = client.read_holding_registers(address=self.POWER_REGISTER, count=self.REGISTER_COUNT)
                if result.isError():
                    self.sense.show_message(f"Tentativo {attempt}: Errore nella lettura registri: {result}", 
                                         text_colour=self.RED, scroll_speed=0.03)
                    continue

                if not hasattr(result, 'registers') or len(result.registers) < self.REGISTER_COUNT:
                    self.sense.show_message(f"Tentativo {attempt}: Lettura registri non andata a buon fine: registri insufficienti.", 
                                         text_colour=self.RED, scroll_speed=0.03)
                    continue

                if len(result.registers) == 1:
                    power_value = result.registers[0]
                else:
                    # Utilizza la funzione di decodifica per valori signed
                    power_value = self.decode_int32_signed(result.registers)
                return power_value

            except Exception as e:
                self.sense.show_message(f"Tentativo {attempt}: Errore nella lettura dall'inverter: {e}.", 
                                     text_colour=self.RED, scroll_speed=0.03)
            finally:
                client.close()

            time.sleep(delay)

        self.sense.show_message("Tutti i tentativi di lettura dall'inverter sono falliti.", 
                             text_colour=self.RED, scroll_speed=0.03)
        return None 

    def read_daily_yield(self):
        """
        Legge il valore di produzione giornaliera dall'inverter.
        Returns:
            float: Valore in kWh o None in caso di errore
        """
        client = ModbusTcpClient(self.INVERTER_IP, port=self.MODBUS_PORT)
        client.unit = 1
        try:
            if not client.connect():
                return None

            result = client.read_holding_registers(address=self.DAILY_YIELD_REGISTER, count=2)
            if result.isError():
                return None

            if not hasattr(result, 'registers') or len(result.registers) < 2:
                return None

            # Combina i due registri e divide per 100 per ottenere i kWh
            value = ((result.registers[0] << 16) | result.registers[1]) / 100.0
            return value

        except Exception as e:
            return None
        finally:
            client.close()

    def read_daily_power_from_file(self):
        """Legge il valore del daily power dal file JSON"""
        try:
            if os.path.exists(self.daily_energy_file):
                with open(self.daily_energy_file, 'r') as f:
                    data = json.load(f)
                    self.last_daily_yield = data['energy_kwh']
                    self.last_daily_yield_time = datetime.strptime(data['timestamp'], "%Y-%m-%d %H:%M:%S")
                    return self.last_daily_yield
        except Exception as e:
            print(f"Errore nella lettura del file daily energy: {e}")
            self.sense.show_message(f"Errore nella lettura del file daily energy: {e}", 
                                 text_colour=self.RED, scroll_speed=0.03)
        return None

    def save_daily_power_to_file(self, energy_kwh):
        """Salva il valore del daily power nel file JSON"""
        try:
            now = datetime.now()
            data = {
                "date": now.strftime("%Y-%m-%d"),
                "energy_kwh": energy_kwh,
                "timestamp": now.strftime("%Y-%m-%d %H:%M:%S")
            }
            with open(self.daily_energy_file, 'w') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            print(f"Errore nel salvataggio del file daily energy: {e}")
            self.sense.show_message(f"Errore nel salvataggio del file daily energy: {e}", 
                                 text_colour=self.RED, scroll_speed=0.03)
        return False

    def update_daily_yield(self):
        """Aggiorna il valore del daily yield alle ore specificate"""
        current_hour = datetime.now().hour
        # Leggi il valore alle 20, 21 e 22
        if current_hour in [20, 21, 22]:
            # Leggi il valore dall'inverter
            value = self.read_daily_yield()
            if value is not None:
                # Salva nel file JSON
                if self.save_daily_power_to_file(value):
                    print(f"Daily yield aggiornato alle {current_hour}:00: {value} kWh")
                    return True
        return False

    def get_last_daily_yield(self):
        """
        Restituisce l'ultimo valore salvato di produzione giornaliera
        """
        return self.last_daily_yield 