#!/usr/bin/env python3
# Questo è lo shebang che indica al sistema che questo script deve essere eseguito con Python 3

# -*- coding: utf-8 -*-
# Specifica l'encoding del file come UTF-8 per supportare caratteri speciali

# Importazione delle librerie necessarie
import csv          # Importa il modulo per gestire i file CSV (valori separati da virgola)
import os           # Importa il modulo per interagire con il sistema operativo
from datetime import datetime, timedelta     # Importa le classi per gestire date, orari e intervalli di tempo
from sense_hat import SenseHat              # Importa la classe per interagire con il sensore SenseHat del Raspberry Pi

class CSVHandler:
    """
    Classe per gestire le operazioni sui file CSV che contengono i dati dell'inverter.
    
    Questa classe fornisce metodi per leggere, scrivere, pulire e analizzare i dati
    contenuti nei file CSV che memorizzano le misurazioni dell'inverter.
    """
    
    def __init__(self, csv_filepath):
        """
        Inizializza un nuovo gestore di file CSV.
        
        Args:
            csv_filepath (str): Il percorso completo del file CSV da gestire
        """
        self.csv_filepath = csv_filepath     # Memorizza il percorso del file CSV come attributo della classe
        self.sense = SenseHat()              # Crea un oggetto SenseHat per mostrare messaggi sul display
        self.sense.set_rotation(180)         # Ruota il display di 180 gradi per visualizzare correttamente i messaggi
        self.RED = (255, 0, 0)               # Definisce il colore rosso in formato RGB (per messaggi di errore)
        self.GREEN = (0, 255, 0)             # Definisce il colore verde in formato RGB (per messaggi di successo)

    def read_csv_data(self):
        """
        Legge il contenuto del file CSV e lo converte in una lista di tuple (timestamp, power).
        
        Returns:
            list: Una lista di tuple, dove ogni tupla contiene (timestamp, power)
                 timestamp è un oggetto datetime e power è un valore numerico
        """
        data = []                            # Inizializza una lista vuota per memorizzare i dati
        if os.path.exists(self.csv_filepath):  # Verifica se il file CSV esiste
            try:
                # Apre il file in modalità lettura con codifica UTF-8
                with open(self.csv_filepath, "r", encoding="utf-8") as f:
                    reader = csv.reader(f)   # Crea un lettore CSV per processare il file
                    for row in reader:       # Itera su ogni riga del file CSV
                        if len(row) >= 2:    # Verifica che la riga abbia almeno 2 colonne (timestamp e power)
                            try:
                                # Converte la stringa del timestamp in un oggetto datetime
                                ts = datetime.strptime(row[0], "%Y_%m_%d_%H:%M")
                                # Converte la seconda colonna in un numero decimale
                                power = float(row[1])
                                # Aggiunge la tupla (timestamp, power) alla lista dei dati
                                data.append((ts, power))
                            except Exception:
                                # Se c'è un errore nella conversione, salta questa riga e continua con la successiva
                                continue
            except Exception as e:
                # Se si verifica un errore durante la lettura del file, mostra un messaggio sul display
                self.sense.show_message("Errore nella lettura del CSV", 
                                     text_colour=self.RED, scroll_speed=0.03)
        return data  # Restituisce la lista di tuple (timestamp, power)

    def append_to_csv(self, timestamp, power):
        """
        Aggiunge una nuova riga con timestamp e power al file CSV.
        
        Args:
            timestamp (str): Il timestamp in formato stringa
            power (float): Il valore di potenza da registrare
        """
        try:
            # Apre il file in modalità append (aggiunta) con codifica UTF-8
            with open(self.csv_filepath, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)       # Crea uno scrittore CSV
                writer.writerow([timestamp, power])  # Scrive una nuova riga con timestamp e power
        except Exception as e:
            # Se si verifica un errore durante la scrittura, mostra un messaggio sul display
            self.sense.show_message("Errore nella scrittura sul CSV", 
                                 text_colour=self.RED, scroll_speed=0.03)

    def cleanup_csv(self):
        """
        Rimuove dal file CSV tutti i dati più vecchi di un anno.
        
        Questo metodo legge l'intero file, filtra i dati mantenendo solo quelli più recenti
        di un anno, e poi riscrive il file con i dati filtrati.
        """
        # Calcola la data limite (un anno fa rispetto ad oggi)
        threshold_date = datetime.now() - timedelta(days=365)
        # Legge tutti i dati dal file CSV
        data = self.read_csv_data()
        # Filtra i dati, mantenendo solo quelli con timestamp successivo alla data limite
        filtered_data = [(ts, power) for ts, power in data if ts >= threshold_date]
        try:
            # Apre il file in modalità scrittura (sovrascrive il contenuto esistente)
            with open(self.csv_filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)  # Crea uno scrittore CSV
                # Scrive ogni tupla filtrata nel file
                for ts, power in filtered_data:
                    writer.writerow([ts.strftime("%Y_%m_%d_%H:%M"), power])
            # Mostra un messaggio di successo sul display
            self.sense.show_message("Cleanup CSV completato", 
                                 text_colour=self.GREEN, scroll_speed=0.03)
        except Exception as e:
            # Se si verifica un errore durante la pulizia, mostra un messaggio sul display
            self.sense.show_message("Errore durante il cleanup del CSV", 
                                 text_colour=self.RED, scroll_speed=0.03)

    def get_day_power_chart(self, num_bars=8, day_start_hour=6, day_end_hour=20):
        """
        Calcola i valori per creare un grafico a barre che rappresenta la potenza durante il giorno.
        
        Questo metodo analizza i dati del giorno corrente (o del giorno precedente se è prima dell'ora
        di inizio) e li suddivide in intervalli per creare un grafico a barre.
        
        Args:
            num_bars (int): Numero di barre nel grafico (default: 8)
            day_start_hour (int): Ora di inizio del periodo diurno (default: 6, cioè le 6:00 del mattino)
            day_end_hour (int): Ora di fine del periodo diurno (default: 20, cioè le 20:00/8:00 PM)
            
        Returns:
            list: Una lista di valori (da 0 a 8) che rappresentano l'altezza di ciascuna barra del grafico
        """
        # Legge tutti i dati dal file CSV
        all_data = self.read_csv_data()
        # Ottiene la data e ora corrente
        now = datetime.now()
        # Determina la data target: se è prima dell'ora di inizio, usa il giorno precedente
        target_date = now.date() if now.hour >= day_start_hour else (now - timedelta(days=1)).date()

        # Calcola il valore massimo di potenza da tutti i dati storici (o 1 se non ci sono dati)
        historical_max = max([power for _, power in all_data]) if all_data else 1

        # Filtra i dati per ottenere solo quelli del giorno target e con potenza positiva
        daylight_data = [(ts, power) for ts, power in all_data
                        if ts.date() == target_date and power > 0]
        
        # Se non ci sono dati per il giorno, restituisce un grafico vuoto (tutte barre a 0)
        if not daylight_data:
            return [0] * num_bars
            
        # Imposta l'orario di inizio e fine per l'analisi (combinando la data target con gli orari specificati)
        start_time = datetime.combine(target_date, datetime.min.time().replace(hour=day_start_hour, minute=0))
        end_time = datetime.combine(target_date, datetime.min.time().replace(hour=day_end_hour, minute=0))
        
        # Calcola l'intervallo totale di tempo in secondi
        total_seconds = (end_time - start_time).total_seconds()
        
        # Crea una lista di liste vuote (bucket) per raggruppare i dati in intervalli temporali
        buckets = [[] for _ in range(num_bars)]
        
        # Distribuisce i dati nei bucket in base all'orario
        for ts, power in daylight_data:
            # Ignora i dati al di fuori dell'intervallo temporale definito
            if ts < start_time or ts > end_time:
                continue
                
            # Calcola quanto tempo è passato dall'inizio dell'intervallo
            elapsed = (ts - start_time).total_seconds()
            # Calcola l'indice del bucket in base alla posizione temporale
            index = min(int((elapsed / total_seconds) * num_bars), num_bars - 1)
            # Aggiunge il valore di potenza al bucket corrispondente
            buckets[index].append(power)
        
        # Calcola il valore medio di potenza per ogni bucket
        avg_values = []
        for bucket in buckets:
            if bucket:  # Se il bucket contiene dati
                avg_values.append(sum(bucket) / len(bucket))  # Calcola la media
            else:  # Se il bucket è vuoto
                avg_values.append(0)  # Imposta il valore a 0
        
        # Converte i valori medi in livelli da 0 a 8 per il grafico a barre
        if historical_max == 0:  # Se il massimo storico è 0
            levels = [0] * num_bars  # Tutti i livelli sono 0
        else:
            # Calcola il livello per ogni valore medio, normalizzando rispetto al massimo storico
            # Usa 8 LED se la media è almeno il 90% del massimo storico
            levels = []
            for val in avg_values:
                ratio = val / historical_max
                if ratio >= 0.9:
                    level = 8
                else:
                    level = min(8, max(0, int(round(ratio * 8))))
                levels.append(level)
            
        return levels  # Restituisce i livelli per il grafico a barre 