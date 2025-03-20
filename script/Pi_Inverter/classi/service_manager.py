#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

class ServiceManager:
    def __init__(self, service_file_path, service_name, python_exec, script_path):
        self.service_file_path = service_file_path
        self.service_name = service_name
        self.python_exec = python_exec
        self.script_path = script_path

    def create_service_file(self):
        """Crea il file di servizio systemd se non esiste."""
        if os.path.exists(self.service_file_path):
            return True

        user = os.getenv("SUDO_USER") or os.getenv("USER") or "root"
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
            with open(self.service_file_path, "w") as f:
                f.write(service_content)
            os.system("systemctl daemon-reload")
            os.system(f"systemctl enable {self.service_name}")
            return True
        except Exception as e:
            print("Errore nella creazione del file di servizio:", e)
            self.sense.show_message(f"Errore nella creazione del file di servizio: {e}", 
                                     text_colour=self.RED, scroll_speed=0.03)
            return False 