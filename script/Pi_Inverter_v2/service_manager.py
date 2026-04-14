#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Creazione/verifica del file di servizio systemd.
NESSUN uso di SenseHat — errori gestiti via print/eccezioni.
Fix del bug originale (self.sense mai inizializzato).
"""

import os

from . import config


class ServiceManager:

    def __init__(self):
        self.service_file_path = config.SERVICE_FILE_PATH
        self.service_name = config.SERVICE_NAME
        self.python_exec = config.PYTHON_EXEC
        self.script_path = config.SCRIPT_PATH

    def create_service_file(self):
        """
        Crea il file di servizio systemd se non esiste gia.
        Restituisce True in caso di successo (anche se esisteva), False su errore.
        """
        if os.path.exists(self.service_file_path):
            return True

        user = os.getenv('SUDO_USER') or os.getenv('USER') or 'root'

        service_content = f"""[Unit]
Description=RBP4 Inverter Monitoring Service
After=network.target

[Service]
ExecStart={self.python_exec} {self.script_path}
Restart=always
User={user}

[Install]
WantedBy=multi-user.target
"""

        try:
            with open(self.service_file_path, 'w') as f:
                f.write(service_content)
            os.system('systemctl daemon-reload')
            os.system(f'systemctl enable {self.service_name}')
            return True
        except Exception as e:
            print(f'Errore nella creazione del file di servizio: {e}')
            return False
