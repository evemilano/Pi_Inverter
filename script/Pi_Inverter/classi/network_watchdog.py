#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NetworkWatchdog - Monitoraggio della connettività di rete con riavvio automatico

Questo modulo implementa un watchdog per monitorare la connettività di rete
e riavviare automaticamente il sistema in caso di perdita di connessione prolungata.

Caratteristiche:
- Controlla sia la connettività locale (gateway) che Internet
- Configurabile: timeout, intervalli di controllo, host da pingare
- Non invasivo: thread separato, logging dettagliato
- Riavvio automatico dopo N tentativi falliti consecutivi
"""

import threading
import time
import subprocess
import socket
import json
from pathlib import Path
from datetime import datetime
import logging


class NetworkWatchdog:
    """
    Watchdog per il monitoraggio della connettività di rete.
    
    Esegue controlli periodici della connettività di rete e può riavviare
    il sistema se la rete rimane irraggiungibile per un periodo prolungato.
    """
    
    def __init__(self, 
                 check_interval=60,          # Intervallo tra i controlli (secondi)
                 max_failures=10,            # Numero massimo di fallimenti consecutivi
                 ping_timeout=5,             # Timeout per ogni ping (secondi)
                 hosts_to_check=None,        # Lista di host da pingare
                 enable_reboot=True,         # Abilita il riavvio automatico
                 logger=None,                # Logger personalizzato
                 config_file=None):          # File di configurazione JSON
        """
        Inizializza il NetworkWatchdog.
        
        Args:
            check_interval (int): Secondi tra un controllo e l'altro
            max_failures (int): Fallimenti consecutivi prima del riavvio
            ping_timeout (int): Timeout in secondi per ogni ping
            hosts_to_check (list): Lista di host da pingare (default: gateway + google.com)
            enable_reboot (bool): Se True, riavvia il sistema dopo max_failures
            logger (logging.Logger): Logger personalizzato (opzionale)
            config_file (str): Percorso al file di configurazione JSON (opzionale)
        """
        # Carica configurazione da file JSON se fornito
        config = self._load_config(config_file) if config_file else {}
        
        # Usa i valori dal file di configurazione se disponibili, altrimenti usa i default
        self.check_interval = config.get('check_interval', check_interval)
        self.max_failures = config.get('max_failures', max_failures)
        self.ping_timeout = config.get('ping_timeout', ping_timeout)
        self.enable_reboot = config.get('enable_reboot', enable_reboot)
        
        # Host da controllare (gateway locale + server pubblico)
        if 'hosts_to_check' in config:
            self.hosts_to_check = config['hosts_to_check']
        elif hosts_to_check is None:
            self.hosts_to_check = [
                self._get_default_gateway(),  # Gateway locale
                "8.8.8.8",                     # Google DNS
                "1.1.1.1"                      # Cloudflare DNS
            ]
        else:
            self.hosts_to_check = hosts_to_check
        
        # Rimuove None dalla lista (nel caso il gateway non sia trovato)
        self.hosts_to_check = [h for h in self.hosts_to_check if h is not None]
        
        # Contatori
        self.consecutive_failures = 0
        self.total_checks = 0
        self.total_failures = 0
        
        # Thread control
        self._stop_event = threading.Event()
        self._thread = None
        
        # Logging
        if logger is None:
            self.logger = self._setup_logger()
        else:
            self.logger = logger
        
        self.logger.info("NetworkWatchdog inizializzato")
        self.logger.info(f"Check interval: {self.check_interval}s, Max failures: {self.max_failures}")
        self.logger.info(f"Host monitorati: {', '.join(self.hosts_to_check)}")
        self.logger.info(f"Riavvio automatico: {'ABILITATO' if self.enable_reboot else 'DISABILITATO'}")
    
    def _load_config(self, config_file):
        """
        Carica la configurazione da un file JSON.
        
        Args:
            config_file (str): Percorso al file di configurazione
            
        Returns:
            dict: Configurazione caricata o dizionario vuoto se il file non esiste
        """
        try:
            config_path = Path(config_file)
            if config_path.exists():
                with open(config_path, 'r') as f:
                    full_config = json.load(f)
                    # Restituisce solo la sezione 'watchdog'
                    config = full_config.get('watchdog', {})
                    
                    # Verifica se il watchdog è abilitato
                    if not config.get('enabled', True):
                        return {}  # Ritorna config vuoto se disabilitato
                    
                    return config
            else:
                print(f"File di configurazione non trovato: {config_file}")
                return {}
        except Exception as e:
            print(f"Errore nel caricamento del file di configurazione: {e}")
            return {}
    
    def _setup_logger(self):
        """Configura il logger per il watchdog."""
        logger = logging.getLogger('NetworkWatchdog')
        logger.setLevel(logging.INFO)
        
        # Handler per file
        try:
            from pathlib import Path
            log_dir = Path.home() / 'Python' / 'script' / 'Pi_Inverter' / 'logs'
            log_dir.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(log_dir / 'network_watchdog.log')
            fh.setLevel(logging.INFO)
            
            # Formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        except Exception as e:
            print(f"Errore nella creazione del log file: {e}")
        
        return logger
    
    def _get_default_gateway(self):
        """
        Ottiene l'indirizzo IP del gateway predefinito.
        
        Returns:
            str: IP del gateway o None se non trovato
        """
        try:
            # Metodo 1: Usando il comando 'ip route'
            result = subprocess.run(
                ['ip', 'route', 'show', 'default'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # Output tipico: "default via 192.168.1.1 dev eth0 ..."
                parts = result.stdout.split()
                if 'via' in parts:
                    gateway_ip = parts[parts.index('via') + 1]
                    return gateway_ip
        except Exception as e:
            self.logger.warning(f"Impossibile ottenere il gateway: {e}")
        
        return None
    
    def _ping_host(self, host):
        """
        Esegue un ping verso un host.
        
        Args:
            host (str): Hostname o IP da pingare
            
        Returns:
            bool: True se il ping ha successo, False altrimenti
        """
        try:
            # Usa 'ping' con 1 pacchetto e timeout specificato
            result = subprocess.run(
                ['ping', '-c', '1', '-W', str(self.ping_timeout), host],
                capture_output=True,
                timeout=self.ping_timeout + 2
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False
        except Exception as e:
            self.logger.warning(f"Errore durante il ping di {host}: {e}")
            return False
    
    def _check_connectivity(self):
        """
        Controlla la connettività di rete pingando gli host configurati.
        
        Returns:
            bool: True se almeno un host risponde, False altrimenti
        """
        self.total_checks += 1
        
        for host in self.hosts_to_check:
            if self._ping_host(host):
                self.logger.debug(f"Ping riuscito verso {host}")
                return True
            else:
                self.logger.debug(f"Ping fallito verso {host}")
        
        return False
    
    def _handle_network_failure(self):
        """
        Gestisce il fallimento della connettività di rete.
        Incrementa i contatori e riavvia il sistema se necessario.
        """
        self.consecutive_failures += 1
        self.total_failures += 1
        
        self.logger.warning(
            f"Rete non raggiungibile! Fallimenti consecutivi: "
            f"{self.consecutive_failures}/{self.max_failures}"
        )
        
        if self.consecutive_failures >= self.max_failures:
            self.logger.critical(
                f"Raggiunto il limite di {self.max_failures} fallimenti consecutivi!"
            )
            
            if self.enable_reboot:
                self.logger.critical("RIAVVIO DEL SISTEMA IN CORSO...")
                self._reboot_system()
            else:
                self.logger.warning("Riavvio disabilitato. Il sistema rimane in esecuzione.")
                # Reset del contatore per evitare log spam
                self.consecutive_failures = 0
    
    def _handle_network_recovery(self):
        """Gestisce il ripristino della connettività di rete."""
        if self.consecutive_failures > 0:
            self.logger.info(
                f"Rete ripristinata dopo {self.consecutive_failures} fallimenti consecutivi"
            )
        self.consecutive_failures = 0
    
    def _reboot_system(self):
        """
        Riavvia il sistema usando il comando 'reboot'.
        Richiede privilegi di root/sudo.
        """
        try:
            self.logger.critical("Esecuzione comando di riavvio...")
            subprocess.run(['sudo', 'reboot'], check=True)
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Errore durante il riavvio del sistema: {e}")
        except Exception as e:
            self.logger.error(f"Errore imprevisto durante il riavvio: {e}")
    
    def _watchdog_loop(self):
        """
        Loop principale del watchdog.
        Controlla periodicamente la connettività di rete.
        """
        self.logger.info("Watchdog avviato")
        
        while not self._stop_event.is_set():
            try:
                if self._check_connectivity():
                    self._handle_network_recovery()
                else:
                    self._handle_network_failure()
                
                # Statistiche periodiche (ogni 100 controlli)
                if self.total_checks % 100 == 0:
                    success_rate = ((self.total_checks - self.total_failures) / 
                                   self.total_checks * 100)
                    self.logger.info(
                        f"Statistiche: {self.total_checks} controlli, "
                        f"{self.total_failures} fallimenti totali, "
                        f"successo: {success_rate:.1f}%"
                    )
                
            except Exception as e:
                self.logger.error(f"Errore nel loop del watchdog: {e}")
            
            # Attende prima del prossimo controllo
            self._stop_event.wait(self.check_interval)
        
        self.logger.info("Watchdog terminato")
    
    def start(self):
        """
        Avvia il watchdog in un thread separato.
        
        Returns:
            bool: True se avviato con successo, False se già in esecuzione
        """
        if self._thread is not None and self._thread.is_alive():
            self.logger.warning("Watchdog già in esecuzione")
            return False
        
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._watchdog_loop,
            daemon=True,
            name="NetworkWatchdog"
        )
        self._thread.start()
        
        self.logger.info("Thread watchdog avviato")
        return True
    
    def stop(self):
        """
        Ferma il watchdog.
        
        Returns:
            bool: True se fermato con successo
        """
        if self._thread is None or not self._thread.is_alive():
            self.logger.warning("Watchdog non in esecuzione")
            return False
        
        self.logger.info("Arresto watchdog...")
        self._stop_event.set()
        self._thread.join(timeout=10)
        
        if self._thread.is_alive():
            self.logger.warning("Il thread watchdog non si è fermato nel timeout previsto")
            return False
        
        self.logger.info("Watchdog fermato correttamente")
        return True
    
    def get_status(self):
        """
        Ottiene lo stato corrente del watchdog.
        
        Returns:
            dict: Dizionario con le statistiche correnti
        """
        return {
            'running': self._thread is not None and self._thread.is_alive(),
            'total_checks': self.total_checks,
            'total_failures': self.total_failures,
            'consecutive_failures': self.consecutive_failures,
            'max_failures': self.max_failures,
            'hosts_monitored': self.hosts_to_check,
            'reboot_enabled': self.enable_reboot
        }


# -------------------- ESEMPIO D'USO --------------------
if __name__ == "__main__":
    # Configurazione del logging per il test
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Test del NetworkWatchdog")
    print("-" * 50)
    
    # Crea il watchdog con configurazione di test
    watchdog = NetworkWatchdog(
        check_interval=10,      # Controlla ogni 10 secondi
        max_failures=3,         # Riavvia dopo 3 fallimenti (30 secondi)
        enable_reboot=False     # Disabilita il riavvio per il test
    )
    
    # Avvia il watchdog
    watchdog.start()
    
    print(f"Watchdog avviato. Premere Ctrl+C per terminare.")
    print(f"Host monitorati: {', '.join(watchdog.hosts_to_check)}")
    print()
    
    try:
        # Mostra lo stato ogni 30 secondi
        while True:
            time.sleep(30)
            status = watchdog.get_status()
            print(f"\nStato attuale:")
            print(f"  - Controlli totali: {status['total_checks']}")
            print(f"  - Fallimenti totali: {status['total_failures']}")
            print(f"  - Fallimenti consecutivi: {status['consecutive_failures']}/{status['max_failures']}")
            
    except KeyboardInterrupt:
        print("\n\nInterruzione ricevuta, arresto del watchdog...")
        watchdog.stop()
        print("Test completato.")
