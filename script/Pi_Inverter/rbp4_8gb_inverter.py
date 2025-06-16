#!/usr/bin/env python3
# Questo è lo shebang che indica al sistema che questo script deve essere eseguito con Python 3

# -*- coding: utf-8 -*-
# Specifica l'encoding del file come UTF-8 per supportare caratteri speciali

# Comandi per gestire il servizio:
# per riavviare il servizio:
# sudo systemctl restart rbp4_8gb_inverter.service

# per eseguire lo script:
# sudo /home/pi/Python/script/Pi_Inverter/venv/bin/python /home/pi/Python/script/Pi_Inverter/rbp4_8gb_inverter.py

'''
Modello: Raspberry Pi 4 Model B Rev 1.5
Architettura: aarch64 (ARM 64-bit)
RAM: 8GB (7.6GB disponibili al sistema)
Sistema operativo: Linux a 64-bit
'''




# Importazione dei moduli standard di Python
import threading    # Per creare ed eseguire thread paralleli
import os           # Per interagire con il sistema operativo
import sys          # Per accedere a variabili e funzioni specifiche del sistema
import time         # Per gestire operazioni legate al tempo e ritardi
from datetime import datetime, timedelta    # Per gestire data e ora e calcolare intervalli di tempo
from sense_hat import SenseHat              # Per interagire con il sensore SenseHat del Raspberry Pi

# Importazione delle classi personalizzate per il monitoraggio dell'inverter
from classi.inverter_monitor import InverterMonitor        # Classe base per il monitoraggio
from classi.daytime_monitor import DaytimeMonitor          # Monitoraggio specifico per il giorno
from classi.nighttime_monitor import NighttimeMonitor      # Monitoraggio specifico per la notte
from classi.service_manager import ServiceManager          # Gestione del servizio systemd
from classi.csv_handler import CSVHandler                  # Gestione dei file CSV

# Inizializzazione dell'interfaccia SenseHat per visualizzare messaggi
sense = SenseHat()      # Crea un'istanza dell'oggetto SenseHat
sense.set_rotation(180) # Ruota il display di 180 gradi per visualizzare correttamente i messaggi

# -------------------- COSTANTI --------------------
# Definizione delle costanti per gli orari di monitoraggio
DAY_START_HOUR = 6      # Ora di inizio del periodo diurno (6:00 del mattino)
DAY_END_HOUR = 20       # Ora di fine del periodo diurno (20:00 - 8:00 pm)

# Definizione dei colori in formato RGB (Rosso, Verde, Blu) per i messaggi sul display
RED = (255, 0, 0)       # Colore rosso (massima intensità)
GREEN = (0, 255, 0)     # Colore verde (massima intensità)
BLACK = (0, 0, 0)       # Colore nero (nessuna luce)

def daily_cleanup(csv_filepath):
    """
    Esegue la pulizia del file CSV una volta al giorno a mezzanotte.
    
    Questa funzione crea un processo in background che attende fino alla mezzanotte
    successiva, poi esegue l'operazione di pulizia sul file CSV. Il processo continua
    a ripetersi indefinitamente, eseguendo la pulizia ogni giorno a mezzanotte.
    
    Args:
        csv_filepath (str): Percorso del file CSV da pulire
    
    Note:
        - Utilizza CSVHandler per gestire le operazioni sul file
        - Il thread rimane in esecuzione fino alla chiusura del programma
        - La funzione cleanup_csv() elimina/archivia i dati vecchi secondo la
          logica implementata nella classe CSVHandler
    """
    csv_handler = CSVHandler(csv_filepath)
    while True:
        # Ottiene l'ora corrente
        now = datetime.now()
        
        # Calcola la prossima mezzanotte (ore 00:00 del giorno successivo)
        next_cleanup = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Calcola quanto tempo manca alla prossima mezzanotte
        sleep_time = (next_cleanup - now).total_seconds()
        
        # Attende fino alla prossima mezzanotte
        time.sleep(sleep_time)
        
        # Esegue la pulizia del file CSV
        csv_handler.cleanup_csv()

def main():
    """
    Funzione principale che gestisce il monitoraggio dell'inverter.
    
    Questa funzione inizializza tutte le componenti necessarie, crea il file di servizio systemd
    se necessario, avvia il thread per la pulizia giornaliera dei file CSV e gestisce il ciclo
    principale di monitoraggio alternando tra modalità diurna e notturna.
    """
    # Inizializza un'istanza della classe InverterMonitor per gestire il monitoraggio dell'inverter
    # e per accedere ai percorsi dei file e alle configurazioni
    inverter_monitor = InverterMonitor()
    
    # Verifica se lo script è in esecuzione come utente root (amministratore)
    if os.geteuid() == 0:
        # Se l'utente è root, crea un gestore per il servizio systemd
        service_manager = ServiceManager(
            inverter_monitor.SERVICE_FILE_PATH,  # Percorso del file di servizio systemd
            inverter_monitor.SERVICE_NAME,       # Nome del servizio systemd
            inverter_monitor.PYTHON_EXEC,        # Percorso dell'eseguibile Python
            inverter_monitor.SCRIPT_PATH         # Percorso dello script corrente
        )
        # Tenta di creare il file di servizio systemd
        if service_manager.create_service_file():
            # Se la creazione ha successo, mostra un messaggio positivo sul display SenseHat
            inverter_monitor.sense.show_message("File di servizio creato con successo.", 
                                    text_colour=inverter_monitor.GREEN, scroll_speed=0.03)
        else:
            # Se la creazione fallisce, mostra un messaggio di errore sul display SenseHat
            inverter_monitor.sense.show_message("Errore nella creazione del file di servizio.", 
                                    text_colour=inverter_monitor.RED, scroll_speed=0.03)
    else:
        # Se l'utente non è root, mostra un avviso sul display SenseHat
        inverter_monitor.sense.show_message("Non in esecuzione come root; il file di servizio NON verra creato.", 
                                text_colour=inverter_monitor.RED, scroll_speed=0.03)

    # Crea un nuovo thread per eseguire la pulizia giornaliera del file CSV a mezzanotte
    cleanup_thread = threading.Thread(
        target=daily_cleanup,                    # Funzione da eseguire nel thread
        args=(inverter_monitor.csv_filepath,),   # Argomenti per la funzione: percorso del file CSV
        daemon=True                              # Imposta come thread daemon (termina quando il programma principale termina)
    )
    # Avvia l'esecuzione del thread di pulizia
    cleanup_thread.start()

    # Mostra un messaggio di avvio sul display SenseHat con informazioni sul polling
    inverter_monitor.sense.show_message(f"Servizio di monitoraggio inverter avviato. Polling ogni {inverter_monitor.POLL_INTERVAL} secondi.", 
                            text_colour=inverter_monitor.GREEN, scroll_speed=0.03)

    # Inizializza il monitor specifico per il periodo diurno
    daytime_monitor = DaytimeMonitor(inverter_monitor.sense, inverter_monitor)
    # Inizializza il monitor specifico per il periodo notturno
    nighttime_monitor = NighttimeMonitor(inverter_monitor.sense, inverter_monitor)
    
    # Ciclo infinito per il monitoraggio continuo
    while True:
        # Ottiene l'ora corrente (solo l'ora, da 0 a 23)
        current_hour = datetime.now().hour
        
        # Verifica se l'ora corrente è compresa nel periodo diurno
        if DAY_START_HOUR <= current_hour < DAY_END_HOUR:
            # Durante il giorno, misura il tempo necessario per l'esecuzione per mantenere un intervallo preciso
            start_time = time.time()  # Memorizza il tempo di inizio dell'esecuzione
            daytime_monitor.update()  # Esegue l'aggiornamento del monitoraggio diurno
            elapsed = time.time() - start_time  # Calcola il tempo trascorso per l'esecuzione
            sleep_time = max(0, inverter_monitor.POLL_INTERVAL - elapsed)  # Calcola il tempo di attesa rimanente
            if sleep_time > 0:
                time.sleep(sleep_time)  # Attende il tempo rimanente per completare l'intervallo di polling
        else:
            # Durante la notte, esegue il monitoraggio notturno
            nighttime_monitor.update()  # Esegue l'aggiornamento del monitoraggio notturno
            time.sleep(inverter_monitor.POLL_INTERVAL)  # Attende per l'intero intervallo di polling


if __name__ == "__main__":
    # Questo blocco viene eseguito solo quando lo script viene avviato direttamente (non quando viene importato)
    main()  # Chiama la funzione principale per avviare il monitoraggio dell'inverter
