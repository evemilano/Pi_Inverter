# Pi_Inverter - Sistema di Monitoraggio Inverter Solare

Sistema completo di monitoraggio per inverter solare **Huawei SUN2000-6KTL-M1** con visualizzazione su **Raspberry Pi 4 (8GB)** dotato di **SenseHat**. Il sistema monitora in tempo reale produzione solare, consumo/immissione dalla rete elettrica, con visualizzazioni dinamiche LED e watchdog di rete integrato.

---

## 📋 Indice

- [Panoramica Sistema](#-panoramica-sistema)
- [Hardware Richiesto](#-hardware-richiesto)
- [Architettura Software](#-architettura-software)
- [Modalità di Funzionamento](#-modalità-di-funzionamento)
- [Sistema di Logging Dati](#-sistema-di-logging-dati)
- [Moduli e Classi](#-moduli-e-classi)
- [Network Watchdog](#-network-watchdog)
- [Installazione e Configurazione](#-installazione-e-configurazione)
- [Gestione Servizio Systemd](#-gestione-servizio-systemd)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Panoramica Sistema

Il sistema Pi_Inverter è una soluzione di monitoraggio completa che:

- **Legge dati inverter** tramite protocollo Modbus TCP
- **Monitora consumo/immissione rete** tramite registro Modbus dedicato
- **Visualizza animazioni LED** su matrice 8x8 RGB del SenseHat
- **Registra dati storici** in file CSV per analisi temporali
- **Gestisce produzione giornaliera** (daily yield) con persistenza JSON
- **Watchdog di rete** con riavvio automatico in caso di disconnessione prolungata
- **Servizio systemd** per esecuzione automatica all'avvio

### Caratteristiche Principali

- ✅ **Doppia modalità**: Diurna (6:00-20:00) e Notturna (20:00-6:00)
- ✅ **Animazioni adattive**: Velocità e luminosità variabili in base alla potenza
- ✅ **Grafico storico**: 8 barre verticali con produzione del giorno
- ✅ **Colori dinamici**: Gradiente rosso→giallo→verde per produzione solare
- ✅ **Logging automatico**: CSV con pulizia automatica dati > 1 anno
- ✅ **Resilienza rete**: Watchdog con ping multipli e riavvio controllato

---

## 🔧 Hardware Richiesto

### Componenti Essenziali

| Componente | Modello | Note |
|------------|---------|------|
| **Computer** | Raspberry Pi 4 Model B (8GB RAM) | Qualsiasi modello Pi 3/4 compatibile |
| **Display/Sensori** | Sense HAT | Matrice LED 8x8 RGB + sensori ambientali |
| **Inverter** | Huawei SUN2000-6KTL-M1 | Deve supportare Modbus TCP |
| **Rete** | Ethernet o WiFi | Connessione stabile richiesta |

### Specifiche Inverter

- **Protocollo**: Modbus TCP
- **Porta**: 502 (default)
- **IP**: 192.168.1.11 (configurabile in [inverter_monitor.py](classi/inverter_monitor.py:18))
- **Registri utilizzati**:
  - `32080`: Potenza solare istantanea (W)
  - `32114`: Produzione giornaliera (kWh × 100)
  - `37113`: Potenza consumo/immissione rete (W)

---

## 🏗️ Architettura Software

### Struttura Directory

```
Pi_Inverter/
├── rbp4_8gb_inverter.py              # Script principale - loop di monitoraggio
├── classi/                            # Moduli Python
│   ├── inverter_monitor.py           # Classe base - comunicazione Modbus
│   ├── daytime_monitor.py            # Monitoraggio diurno (6-20)
│   ├── nighttime_monitor.py          # Monitoraggio notturno (20-6)
│   ├── led_controller.py             # Gestione matrice LED e animazioni
│   ├── csv_handler.py                # Lettura/scrittura/pulizia CSV
│   ├── apc_monitor.py                # Lettura consumo/immissione rete
│   ├── network_watchdog.py           # Watchdog connettività rete
│   └── service_manager.py            # Creazione servizio systemd
├── logs/                              # File di log e dati
│   ├── power_log.csv                 # Produzione solare (timestamp, W)
│   ├── power_cons_log.csv            # Consumo rete (timestamp, kW)
│   └── network_watchdog.log          # Log watchdog rete
├── network_watchdog_config.json       # Configurazione watchdog
├── last_daily_energy.json             # Produzione giornaliera corrente
└── README.md                          # Questa documentazione
```

### Flusso di Esecuzione

```
Avvio rbp4_8gb_inverter.py
    ↓
Inizializzazione InverterMonitor
    ├─ Connessione Modbus inverter (192.168.1.11:502)
    ├─ Caricamento configurazioni
    └─ Setup percorsi file CSV/JSON
    ↓
Creazione Servizio Systemd (se eseguito come root)
    ├─ Genera /etc/systemd/system/rbp4_8gb_inverter.service
    ├─ Abilita avvio automatico
    └─ Reload daemon systemd
    ↓
Avvio Thread Cleanup CSV (daemon)
    ├─ Calcola tempo a prossima mezzanotte
    ├─ Sleep fino a 00:00
    └─ Rimuove dati CSV > 1 anno
    ↓
Avvio Network Watchdog (background thread)
    ├─ Carica network_watchdog_config.json
    ├─ Ping gateway + DNS pubblici ogni N secondi
    └─ Riavvio sistema dopo M fallimenti consecutivi
    ↓
Inizializzazione Monitor Giorno/Notte
    ├─ DaytimeMonitor (CSV solare + CSV rete + LED doppia barra)
    └─ NighttimeMonitor (CSV + daily yield + grafico)
    ↓
Loop Infinito (polling ogni 60s)
    ├─ if 06:00 ≤ ora < 20:00 → DaytimeMonitor.update()
    │   ├─ Query inverter (registro 32080)
    │   ├─ Query consumo rete (registro 37113)
    │   ├─ Append to power_log.csv
    │   ├─ Append to power_cons_log.csv
    │   ├─ Calcola livelli LED (1-8) da valori storici
    │   ├─ Mostra messaggi ("Sol: X.X kW", "Rete: X.X kW")
    │   └─ Animazione doppia barra LED (4+4 colonne, effetto onda)
    │
    └─ if 20:00 ≤ ora < 06:00 → NighttimeMonitor.update()
        ├─ if ora ∈ {20, 21, 22} → Aggiorna daily yield
        │   ├─ Leggi registro 32114 inverter
        │   └─ Salva in last_daily_energy.json
        ├─ Mostra messaggio "Daily power: X.XX kWh" × 2
        ├─ Query consumo rete + animazione barra 8 colonne
        └─ Grafico produzione giornaliera (8 barre verticali)
```

---

## ⏰ Modalità di Funzionamento

### 🌞 Modalità DIURNA (6:00 - 20:00)

Ciclo ogni **60 secondi**:

1. **Query Inverter Solare**
   - Registro Modbus: `32080` (potenza istantanea)
   - Decodifica: Int32 signed → Watt
   - Retry: 3 tentativi con delay 1s

2. **Query Consumo Rete**
   - Registro Modbus: `37113` (potenza consumo/immissione)
   - Decodifica: Int32 signed / 1000 → kW
   - Valori positivi: Consumo dalla rete (BLUE)
   - Valori negativi: Immissione in rete (RED)

3. **Salvataggio Dati CSV**
   - `power_log.csv`: `2025_03_20_14:30,4520.0` (timestamp, W)
   - `power_cons_log.csv`: `2025_03_20_14:30,2.345` (timestamp, kW)

4. **Calcolo Livelli LED**
   - Legge valori storici da CSV
   - Normalizza valore corrente rispetto al max storico
   - Formula: `level = round((current / max_historical) × 8)`
   - Range: 1-8 LED verticali

5. **Visualizzazione Messaggi**
   - **Messaggio Solare**: `"Sol: 4.5 kW"`
     - Colore: Gradiente dinamico
       - `ratio < 0.5`: Rosso → Giallo
       - `ratio ≥ 0.5`: Giallo → Verde
   - **Messaggio Rete**: `"Rete: 2.3 kW"` o `"Rete: -1.8 kW"`
     - Colore: BLU (consumo) / ROSSO (immissione)

6. **Animazione Doppia Barra**
   - **Colonne 0-3**: Produzione solare (verde/giallo/rosso)
   - **Colonne 4-7**: Consumo rete (blu/rosso)
   - **Effetto onda**: Luminosità pulsante 40%-100%
   - **Velocità adattiva**: Più potenza = animazione più veloce
   - **Cicli**: 20-40 cicli (15-30 secondi totali)

### 🌙 Modalità NOTTURNA (20:00 - 6:00)

Ciclo ogni **60 secondi**:

1. **Aggiornamento Daily Yield** (se ora = 20, 21 o 22)
   - Legge registro `32114` inverter
   - Decodifica: `((reg[0] << 16) | reg[1]) / 100.0` → kWh
   - Salva in `last_daily_energy.json`:
     ```json
     {
       "date": "2026-02-01",
       "energy_kwh": 13.16,
       "timestamp": "2026-02-01 20:15:34"
     }
     ```

2. **Sequenza Visualizzazione** (3 fasi):

   **FASE 1: Messaggio Daily Yield (~9s)**
   ```
   Mostra × 2: "Daily power: 13.16 kWh" (bianco)
   ```

   **FASE 2: Barra Consumo Rete (~20-50s)**
   ```
   - Query registro 37113 (consumo corrente)
   - Calcola livello 1-8 da valori storici CSV
   - Mostra messaggio: "Rete: X.X kW"
   - Animazione barra 8 colonne (full-width)
   - Effetto onda con colore auto (blu/rosso)
   ```

   **FASE 3: Grafico Produzione Giornaliera (~25-50s)**
   ```
   - Legge power_log.csv del giorno appena concluso
   - Divide giornata in 8 intervalli (6:00-20:00 → 8 barre)
   - Calcola media potenza per ogni intervallo
   - Normalizza rispetto al max storico
   - 8 barre verticali colorate (gradiente caldo→freddo)
   ```

---

## 📊 Sistema di Logging Dati

### File CSV Generati

#### 1. `power_log.csv` - Produzione Solare

- **Formato**: `Timestamp,Power (W)`
- **Esempio**:
  ```csv
  2025_03_20_09:46,3018.0
  2025_03_20_09:47,3037.0
  2025_03_20_09:48,3052.0
  ```
- **Frequenza**: Ogni 60 secondi (solo periodo 6:00-20:00)
- **Utilizzo**:
  - Calcolo livelli barra solare LED
  - Generazione grafico notturno 8 barre
  - Normalizzazione valori rispetto allo storico

#### 2. `power_cons_log.csv` - Consumo/Immissione Rete

- **Formato**: `Timestamp,Power (kW)`
- **Esempio**:
  ```csv
  2025_03_20_10:56,3.627
  2025_03_20_10:57,3.643
  2025_03_20_10:58,-1.234
  ```
- **Frequenza**: Ogni 60 secondi (periodo 6:00-20:00)
- **Valori**:
  - Positivi: Consumo dalla rete
  - Negativi: Immissione in rete
- **Utilizzo**:
  - Calcolo livelli barra rete LED
  - Visualizzazione notturna consumo

### Pulizia Automatica CSV

**Funzione**: `daily_cleanup(csv_filepath)` ([rbp4_8gb_inverter.py:54](rbp4_8gb_inverter.py:54))

- **Timing**: Eseguita a mezzanotte (00:00) ogni giorno
- **Thread**: Daemon separato (non blocca main loop)
- **Logica**:
  ```python
  threshold_date = datetime.now() - timedelta(days=365)
  filtered_data = [(ts, power) for ts, power in data if ts >= threshold_date]
  ```
- **Effetto**: Rimuove tutti i dati più vecchi di 1 anno
- **File interessati**:
  - `logs/power_log.csv`
  - `logs/power_cons_log.csv` (via CSVHandler istanziato separatamente)

### File JSON Produzione Giornaliera

**File**: `last_daily_energy.json`

- **Struttura**:
  ```json
  {
    "date": "2026-02-01",
    "energy_kwh": 13.16,
    "timestamp": "2026-02-01 22:57:53"
  }
  ```
- **Aggiornamento**: Ore 20:00, 21:00, 22:00 (3 tentativi)
- **Persistenza**: Mantiene ultimo valore valido tra riavvii
- **Lettura**: All'inizializzazione di `NighttimeMonitor`
- **Funzioni**:
  - `save_daily_power_to_file(energy_kwh)` ([inverter_monitor.py:149](classi/inverter_monitor.py:149))
  - `read_daily_power_from_file()` ([inverter_monitor.py:134](classi/inverter_monitor.py:134))

---

## 🔌 Moduli e Classi

### 1. `inverter_monitor.py` - Classe Base

**Responsabilità**: Comunicazione Modbus, configurazione globale, gestione daily yield

**Attributi chiave**:
```python
INVERTER_IP = "192.168.1.11"
MODBUS_PORT = 502
POWER_REGISTER = 32080          # Potenza istantanea (W)
DAILY_YIELD_REGISTER = 32114    # Produzione giornaliera (kWh × 100)
POLL_INTERVAL = 60              # Secondi tra query
```

**Metodi principali**:

- **`decode_int32_signed(registers)`** ([riga 48](classi/inverter_monitor.py:48))
  - Input: Lista di 2 registri a 16 bit
  - Output: Intero signed a 32 bit
  - Gestione: Complemento a 2 per valori negativi

- **`query_inverter(max_retries=3, delay=1)`** ([riga 65](classi/inverter_monitor.py:65))
  - Connessione Modbus TCP
  - Lettura registro 32080 (potenza solare)
  - Retry automatico con delay
  - Fallback: `None` dopo 3 tentativi

- **`read_daily_yield()`** ([riga 106](classi/inverter_monitor.py:106))
  - Lettura registro 32114
  - Conversione: `value / 100.0` → kWh
  - Return: `float` o `None`

- **`update_daily_yield()`** ([riga 167](classi/inverter_monitor.py:167))
  - Verifica ora corrente (20, 21, 22)
  - Chiamata `read_daily_yield()`
  - Salvataggio JSON via `save_daily_power_to_file()`

### 2. `daytime_monitor.py` - Monitoraggio Diurno

**Responsabilità**: Query periodica inverter/rete, logging CSV, visualizzazione doppia barra

**Metodo principale**: `update()` ([riga 23](classi/daytime_monitor.py:23))

```python
def update(self):
    # 1. Timestamp corrente
    timestamp = datetime.now().strftime("%Y_%m_%d_%H:%M")

    # 2. Query inverter solare
    solar_power = self.inverter_monitor.query_inverter()  # W

    # 3. Query consumo rete
    grid_power = self.apc_monitor.get_power_consumption()  # kW

    # 4. Salvataggio CSV
    self.csv_handler.append_to_csv(timestamp, solar_power)
    self.grid_csv_handler.append_to_csv(timestamp, grid_power)

    # 5. Calcolo livelli LED
    solar_historical = [p for _, p in self.csv_handler.read_csv_data()]
    solar_level = self.led_controller.calculate_level(solar_power, solar_historical)
    grid_level = self.led_controller.calculate_level(grid_power, grid_historical)

    # 6. Visualizzazione
    solar_color = self.led_controller.choose_color(solar_power, solar_historical)
    self.led_controller.show_message(f"Sol: {solar_power/1000:.1f} kW", color=solar_color)
    self.led_controller.show_message(f"Rete: {grid_power:.1f} kW", color=...)
    self.led_controller.update_led_matrix(solar_level, grid_level, solar_color)
```

### 3. `nighttime_monitor.py` - Monitoraggio Notturno

**Responsabilità**: Aggiornamento daily yield, visualizzazione grafico/barra notturna

**Metodo principale**: `update()` ([riga 34](classi/nighttime_monitor.py:34))

```python
def update(self):
    # 1. Tenta aggiornamento daily yield (se ora corretta)
    if self.inverter_monitor.update_daily_yield():
        self.last_daily_yield = self.inverter_monitor.read_daily_power_from_file()

    # 2. Sequenza visualizzazione
    self.display_daily_yield()      # Messaggio × 2 (~9s)
    time.sleep(1)
    self.display_grid_bar()         # Barra rete 8 col (~20-50s)
    time.sleep(1)
    self.display_graph()            # Grafico 8 barre (~25-50s)
```

**Funzioni visualizzazione**:

- **`display_daily_yield()`** ([riga 55](classi/nighttime_monitor.py:55))
  - Testo: `"Daily power: 13.16 kWh"`
  - Colore: Bianco (255, 255, 255)
  - Ripetizioni: 2 volte

- **`display_grid_bar()`** ([riga 62](classi/nighttime_monitor.py:62))
  - Query consumo corrente
  - Calcolo livello 1-8
  - Messaggio + animazione barra full-width

- **`display_graph()`** ([riga 84](classi/nighttime_monitor.py:84))
  - Chiamata `csv_handler.get_day_power_chart(num_bars=8)`
  - Visualizzazione grafico statico 8 barre

### 4. `led_controller.py` - Gestione LED

**Responsabilità**: Animazioni LED, calcolo livelli, scelta colori

**Metodi chiave**:

- **`update_led_matrix(solar_level, grid_level, solar_color)`** ([riga 35](classi/led_controller.py:35))
  - Doppia barra verticale (4 + 4 colonne)
  - Effetto onda con luminosità pulsante
  - Velocità adattiva: `wave_speed = 0.3 × (1 - 0.7 × ratio)`
  - Cicli: `20 + (20 × ratio)` → range 20-40

- **`update_single_bar(level, color_mode='auto')`** ([riga 107](classi/led_controller.py:107))
  - Barra singola 8 colonne (full-width)
  - Modalità colore: 'blue', 'red', 'auto', o tupla RGB
  - Stesso effetto onda di `update_led_matrix`

- **`update_bar_chart(bar_values, color)`** ([riga 17](classi/led_controller.py:17))
  - Grafico a barre statico
  - Input: Lista di 8 valori (0-8)
  - Colore gradiente: Caldo (rosso/giallo) → Freddo (blu)

- **`calculate_level(current_power, historical_values)`** ([riga 160](classi/led_controller.py:160))
  - Normalizzazione valore corrente vs max storico
  - Gestione separata valori positivi/negativi
  - Formula: `round((current / max) × 8)`
  - Range output: 0-8

- **`choose_color(current_power, historical_values)`** ([riga 187](classi/led_controller.py:187))
  - Gradiente dinamico rosso → giallo → verde
  - Basato su `ratio = current / max_historical`
  - Logica:
    ```python
    if ratio < 0.5:
        r = 255
        g = int(510 × ratio)      # 0 → 255
    else:
        r = int(510 × (1 - ratio)) # 255 → 0
        g = 255
    ```

### 5. `csv_handler.py` - Gestione CSV

**Responsabilità**: Lettura, scrittura, pulizia, analisi dati CSV

**Metodi principali**:

- **`read_csv_data()`** ([riga 34](classi/csv_handler.py:34))
  - Return: Lista di tuple `[(datetime, float), ...]`
  - Parsing: `datetime.strptime(row[0], "%Y_%m_%d_%H:%M")`

- **`append_to_csv(timestamp, power)`** ([riga 66](classi/csv_handler.py:66))
  - Append mode con `newline=""`
  - Encoding: UTF-8

- **`cleanup_csv()`** ([riga 84](classi/csv_handler.py:84))
  - Threshold: `datetime.now() - timedelta(days=365)`
  - Filtro + riscrittura file completo

- **`get_day_power_chart(num_bars=8, day_start_hour=6, day_end_hour=20)`** ([riga 112](classi/csv_handler.py:112))
  - Filtra dati giorno target (corrente o precedente)
  - Divide in `num_bars` intervalli temporali
  - Calcola media per bucket
  - Normalizza vs max storico → livelli 0-8
  - Return: `[4, 6, 7, 8, 7, 5, 3, 1]` (esempio)

### 6. `apc_monitor.py` - Monitoraggio Rete

**Responsabilità**: Lettura consumo/immissione rete da registro Modbus

**Configurazione**:
```python
INVERTER_IP = "192.168.1.11"
MODBUS_PORT = 502
TARGET_REGISTER = 37113  # Potenza rete (W signed)
```

**Metodo principale**:

- **`get_power_consumption()`** ([riga 48](classi/apc_monitor.py:48))
  - Legge 2 registri da 37113
  - Decodifica Int32 signed
  - Conversione: `value / 1000.0` → kW
  - Retry: 3 tentativi
  - Fallback: `0.0`

### 7. `service_manager.py` - Gestione Systemd

**Responsabilità**: Creazione automatica file di servizio systemd

**Metodo**:

- **`create_service_file()`** ([riga 14](classi/service_manager.py:14))
  - Verifica esistenza file
  - Genera contenuto servizio:
    ```ini
    [Unit]
    Description=RBP4 Inverter Monitoring Service
    After=network.target

    [Service]
    ExecStart=/path/to/python /path/to/script.py
    Restart=always
    User=pi

    [Install]
    WantedBy=multi-user.target
    ```
  - Esegue `systemctl daemon-reload`
  - Abilita servizio: `systemctl enable rbp4_8gb_inverter.service`

---

## 🌐 Network Watchdog

Sistema di monitoraggio connettività con riavvio automatico del sistema.

### Funzionamento

1. **Controllo Periodico** (default: ogni 120 secondi)
   - Ping gateway locale (rilevato automaticamente via `ip route`)
   - Ping Google DNS (8.8.8.8)
   - Ping Cloudflare DNS (1.1.1.1)

2. **Logica Fallimento**
   - **Fallimento**: Tutti gli host irraggiungibili
   - **Successo**: Almeno 1 host risponde
   - **Contatore**: Incremento solo se fallimenti consecutivi

3. **Riavvio Automatico**
   - Dopo N fallimenti consecutivi (default: 10)
   - Tempo offline: `check_interval × max_failures` = 120s × 10 = **20 minuti**
   - Comando: `sudo reboot`

### Configurazione

**File**: `network_watchdog_config.json`

```json
{
  "watchdog": {
    "enabled": true,
    "check_interval": 120,
    "max_failures": 10,
    "ping_timeout": 10,
    "enable_reboot": true,
    "hosts_to_check": ["8.8.8.8", "1.1.1.1"]
  }
}
```

**Parametri**:

| Parametro | Tipo | Default | Descrizione |
|-----------|------|---------|-------------|
| `enabled` | bool | true | Abilita/disabilita watchdog |
| `check_interval` | int | 120 | Secondi tra controlli |
| `max_failures` | int | 10 | Fallimenti prima riavvio |
| `ping_timeout` | int | 10 | Timeout ping (secondi) |
| `enable_reboot` | bool | true | Abilita riavvio automatico |
| `hosts_to_check` | array | ["8.8.8.8","1.1.1.1"] | IP da pingare |

### Profili Preconfigurati

#### Conservativo (30 minuti offline)
```json
{
  "watchdog": {
    "check_interval": 120,
    "max_failures": 15
  }
}
```

#### Moderato - DEFAULT (20 minuti offline)
```json
{
  "watchdog": {
    "check_interval": 120,
    "max_failures": 10
  }
}
```

#### Aggressivo (3 minuti offline)
```json
{
  "watchdog": {
    "check_interval": 30,
    "max_failures": 6
  }
}
```

### Logging

**File**: `logs/network_watchdog.log`

**Formato**:
```
2026-02-01 18:30:15 - NetworkWatchdog - INFO - NetworkWatchdog inizializzato
2026-02-01 18:30:15 - NetworkWatchdog - INFO - Check interval: 120s, Max failures: 10
2026-02-01 18:30:15 - NetworkWatchdog - INFO - Host monitorati: 192.168.1.1, 8.8.8.8, 1.1.1.1
2026-02-01 18:35:20 - NetworkWatchdog - WARNING - Rete non raggiungibile! Fallimenti consecutivi: 1/10
2026-02-01 18:54:20 - NetworkWatchdog - CRITICAL - Raggiunto il limite di 10 fallimenti consecutivi!
2026-02-01 18:54:20 - NetworkWatchdog - CRITICAL - RIAVVIO DEL SISTEMA IN CORSO...
```

### Monitoraggio Real-Time

```bash
# Log in tempo reale
tail -f /home/pi/Python/script/Pi_Inverter/logs/network_watchdog.log

# Statistiche watchdog (ogni 100 controlli)
grep "Statistiche" logs/network_watchdog.log
```

### Test Senza Riavvio

```json
{
  "watchdog": {
    "enabled": true,
    "enable_reboot": false,
    "check_interval": 10,
    "max_failures": 3
  }
}
```

### Permessi Sudo

Il watchdog richiede permessi sudo per `reboot`:

```bash
sudo visudo
```

Aggiungi riga:
```
pi ALL=(ALL) NOPASSWD: /sbin/reboot
```

---

## 🚀 Installazione e Configurazione

### Dipendenze Software

```bash
# Aggiorna sistema
sudo apt update && sudo apt upgrade -y

# Installa Python 3 e pip
sudo apt install python3 python3-pip python3-venv -y

# Crea virtual environment
cd /home/pi/Python/script/Pi_Inverter
python3 -m venv venv

# Attiva venv
source venv/bin/activate

# Installa dipendenze
pip install sense-hat pymodbus
```

### Configurazione Inverter

Modifica IP inverter in [classi/inverter_monitor.py](classi/inverter_monitor.py:18):

```python
self.INVERTER_IP = "192.168.1.11"  # ← Modifica qui
```

### Configurazione Watchdog

Modifica [network_watchdog_config.json](network_watchdog_config.json):

```json
{
  "watchdog": {
    "enabled": true,
    "check_interval": 120,
    "max_failures": 10
  }
}
```

### Test Manuale

```bash
# Con virtual environment
cd /home/pi/Python/script/Pi_Inverter
source venv/bin/activate
python rbp4_8gb_inverter.py

# Oppure direttamente
sudo /home/pi/Python/script/Pi_Inverter/venv/bin/python \
     /home/pi/Python/script/Pi_Inverter/rbp4_8gb_inverter.py
```

---

## 🔧 Gestione Servizio Systemd

### Creazione Servizio

Il servizio viene creato automaticamente al primo avvio come root:

```bash
sudo /home/pi/Python/script/Pi_Inverter/venv/bin/python \
     /home/pi/Python/script/Pi_Inverter/rbp4_8gb_inverter.py
```

File generato: `/etc/systemd/system/rbp4_8gb_inverter.service`

### Comandi Gestione

```bash
# Riavvia servizio
sudo systemctl restart rbp4_8gb_inverter.service

# Visualizza status
sudo systemctl status rbp4_8gb_inverter.service

# Stop servizio
sudo systemctl stop rbp4_8gb_inverter.service

# Start servizio
sudo systemctl start rbp4_8gb_inverter.service

# Disabilita avvio automatico
sudo systemctl disable rbp4_8gb_inverter.service

# Riabilita avvio automatico
sudo systemctl enable rbp4_8gb_inverter.service
```

### Visualizzazione Log

```bash
# Log in tempo reale
journalctl -u rbp4_8gb_inverter.service -f

# Ultime 50 righe
journalctl -u rbp4_8gb_inverter.service -n 50

# Log da oggi
journalctl -u rbp4_8gb_inverter.service --since today

# Log con timestamp specifico
journalctl -u rbp4_8gb_inverter.service --since "2026-02-01 18:00:00"
```

---

## 🐛 Troubleshooting

### Il servizio non si avvia

```bash
# Controlla errori systemd
journalctl -u rbp4_8gb_inverter.service -n 50

# Verifica permessi file
ls -la /home/pi/Python/script/Pi_Inverter/rbp4_8gb_inverter.py

# Test connessione inverter
ping 192.168.1.11

# Test Modbus manuale
python3 -c "
from pymodbus.client import ModbusTcpClient
client = ModbusTcpClient('192.168.1.11', port=502)
client.unit = 1
if client.connect():
    result = client.read_holding_registers(32080, 2)
    print('OK:', result.registers if hasattr(result, 'registers') else 'Errore')
client.close()
"
```

### Display LED non funziona

```bash
# Test SenseHat
python3 -c "from sense_hat import SenseHat; s=SenseHat(); s.show_message('TEST')"

# Verifica moduli I2C
sudo i2cdetect -y 1

# Riavvia SenseHat
sudo systemctl restart rbp4_8gb_inverter.service
```

### CSV non salvati

```bash
# Verifica directory logs
ls -la /home/pi/Python/script/Pi_Inverter/logs/

# Controlla permessi scrittura
touch /home/pi/Python/script/Pi_Inverter/logs/test.txt
rm /home/pi/Python/script/Pi_Inverter/logs/test.txt

# Verifica spazio disco
df -h /home/pi/Python/script/Pi_Inverter/logs/
```

### Watchdog non riavvia

```bash
# Controlla log watchdog
tail -100 /home/pi/Python/script/Pi_Inverter/logs/network_watchdog.log

# Verifica permessi sudo
sudo -l | grep reboot

# Test configurazione JSON
python3 -c "import json; print(json.load(open('/home/pi/Python/script/Pi_Inverter/network_watchdog_config.json')))"

# Verifica enable_reboot
grep "enable_reboot" /home/pi/Python/script/Pi_Inverter/network_watchdog_config.json
```

### Inverter non risponde

```bash
# Verifica connessione di rete
ping 192.168.1.11

# Controlla porta Modbus
nc -zv 192.168.1.11 502

# Test con timeout maggiore
# Modifica in inverter_monitor.py: POLL_INTERVAL = 120
```

---

## 📈 Note Tecniche

- **Thread Safety**: Cleanup CSV in thread daemon separato
- **Modbus Timeout**: 10 secondi per evitare blocchi
- **Error Handling**: Fallback a 0 se inverter non risponde
- **Rotazione Display**: SenseHat ruotato 180° ([rbp4_8gb_inverter.py:42](rbp4_8gb_inverter.py:42))
- **Encoding**: UTF-8 per supporto caratteri speciali
- **Polling Adattivo**: Sleep calcolato dinamicamente per mantenere intervallo preciso

---

## 📄 Informazioni Versione

- **Versione**: 3.0
- **Ultimo aggiornamento**: 2026-02-01
- **Hardware**: Raspberry Pi 4B 8GB + SenseHat
- **Inverter**: Huawei SUN2000-6KTL-M1
- **Python**: 3.x (testato su 3.9+)
- **Sistema Operativo**: Raspberry Pi OS (Debian-based)

---

## 📞 Supporto

Per problemi o domande:
1. Verifica log: `journalctl -u rbp4_8gb_inverter.service -n 100`
2. Controlla file log: `logs/network_watchdog.log`
3. Test manuale: Esegui script direttamente per vedere errori in tempo reale
