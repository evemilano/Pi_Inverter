# Network Watchdog - Documentazione

## 📋 Panoramica

Il **Network Watchdog** è un modulo plug-and-play che monitora la connettività di rete del Raspberry Pi e riavvia automaticamente il sistema in caso di perdita di connessione prolungata.

## ✨ Caratteristiche

- ✅ **Non invasivo**: Lavora in un thread separato senza interferire con l'applicazione principale
- ✅ **Configurabile**: Tutte le impostazioni possono essere modificate tramite file JSON
- ✅ **Logging dettagliato**: Registra tutti gli eventi in un file di log
- ✅ **Ping multipli**: Controlla più host (gateway locale + DNS pubblici)
- ✅ **Riavvio controllato**: Riavvia solo dopo N fallimenti consecutivi
- ✅ **Test mode**: Può essere disabilitato per test senza riavvio

## 🚀 Come Funziona

1. Il watchdog controlla la connettività di rete ogni X secondi (default: 60s)
2. Prova a pingare diversi host:
   - Gateway locale (router)
   - Google DNS (8.8.8.8)
   - Cloudflare DNS (1.1.1.1)
3. Se **tutti** gli host sono irraggiungibili → conta come un fallimento
4. Dopo N fallimenti consecutivi (default: 10) → riavvia il sistema
5. Se la rete torna prima dei N fallimenti → resetta il contatore

### Esempio pratico

Con la configurazione di default:
- Controllo ogni 60 secondi
- 10 fallimenti massimi
- **Risultato**: Il sistema si riavvia se la rete è offline per circa **10 minuti**

## ⚙️ Configurazione

### File di configurazione

Il file `network_watchdog_config.json` contiene tutte le impostazioni:

```json
{
  "watchdog": {
    "enabled": true,
    "check_interval": 60,
    "max_failures": 10,
    "ping_timeout": 5,
    "enable_reboot": true,
    "hosts_to_check": [
      "8.8.8.8",
      "1.1.1.1"
    ]
  }
}
```

### Parametri

| Parametro | Tipo | Default | Descrizione |
|-----------|------|---------|-------------|
| `enabled` | bool | true | Abilita/disabilita il watchdog |
| `check_interval` | int | 60 | Secondi tra ogni controllo |
| `max_failures` | int | 10 | Fallimenti consecutivi prima del riavvio |
| `ping_timeout` | int | 5 | Timeout in secondi per ogni ping |
| `enable_reboot` | bool | true | Abilita il riavvio automatico |
| `hosts_to_check` | array | ["8.8.8.8","1.1.1.1"] | Lista di IP da pingare |

### Configurazioni Preconfigurate

#### 1️⃣ Conservativa (30 minuti offline)
```json
{
  "watchdog": {
    "enabled": true,
    "check_interval": 120,
    "max_failures": 15,
    "enable_reboot": true
  }
}
```
- Controllo ogni 2 minuti
- Riavvio dopo 15 fallimenti = **30 minuti offline**

#### 2️⃣ Moderata - DEFAULT (10 minuti offline)
```json
{
  "watchdog": {
    "enabled": true,
    "check_interval": 60,
    "max_failures": 10,
    "enable_reboot": true
  }
}
```
- Controllo ogni minuto
- Riavvio dopo 10 fallimenti = **10 minuti offline**

#### 3️⃣ Aggressiva (3 minuti offline)
```json
{
  "watchdog": {
    "enabled": true,
    "check_interval": 30,
    "max_failures": 6,
    "enable_reboot": true
  }
}
```
- Controllo ogni 30 secondi
- Riavvio dopo 6 fallimenti = **3 minuti offline**

## 🔧 Modifica della Configurazione

1. **Apri il file di configurazione**:
   ```bash
   nano /home/pi/Python/script/Pi_Inverter/network_watchdog_config.json
   ```

2. **Modifica i parametri** secondo le tue esigenze

3. **Riavvia il servizio**:
   ```bash
   sudo systemctl restart rbp4_8gb_inverter.service
   ```

## 📊 Monitoraggio

### Log File

I log del watchdog sono salvati in:
```
/home/pi/Python/script/Pi_Inverter/logs/network_watchdog.log
```

### Visualizzare i log in tempo reale:
```bash
tail -f /home/pi/Python/script/Pi_Inverter/logs/network_watchdog.log
```

### Esempi di log:

```
2025-11-12 18:30:15 - NetworkWatchdog - INFO - NetworkWatchdog inizializzato
2025-11-12 18:30:15 - NetworkWatchdog - INFO - Check interval: 60s, Max failures: 10
2025-11-12 18:30:15 - NetworkWatchdog - INFO - Host monitorati: 192.168.1.1, 8.8.8.8, 1.1.1.1
2025-11-12 18:30:15 - NetworkWatchdog - INFO - Watchdog avviato

# Se la rete va offline:
2025-11-12 18:35:20 - NetworkWatchdog - WARNING - Rete non raggiungibile! Fallimenti consecutivi: 1/10
2025-11-12 18:36:20 - NetworkWatchdog - WARNING - Rete non raggiungibile! Fallimenti consecutivi: 2/10
...
2025-11-12 18:44:20 - NetworkWatchdog - WARNING - Rete non raggiungibile! Fallimenti consecutivi: 10/10
2025-11-12 18:44:20 - NetworkWatchdog - CRITICAL - Raggiunto il limite di 10 fallimenti consecutivi!
2025-11-12 18:44:20 - NetworkWatchdog - CRITICAL - RIAVVIO DEL SISTEMA IN CORSO...

# Se la rete torna online:
2025-11-12 18:35:20 - NetworkWatchdog - INFO - Rete ripristinata dopo 3 fallimenti consecutivi
```

## 🧪 Test e Debug

### Disabilitare temporaneamente il watchdog

Modifica il file di configurazione:
```json
{
  "watchdog": {
    "enabled": false
  }
}
```

### Testare senza riavvio

Per testare il watchdog senza che riavvii il sistema:
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

Questo configurazione:
- Controlla ogni 10 secondi
- Registra i fallimenti ma NON riavvia
- Ottimo per verificare che il watchdog funzioni correttamente

### Test manuale

Per testare il watchdog manualmente, puoi eseguire:

```bash
cd /home/pi/Python/script/Pi_Inverter
python3 -m classi.network_watchdog
```

Questo avvierà il watchdog in modalità test.

## 🔒 Sicurezza

### Permessi sudo

Il watchdog richiede permessi sudo per riavviare il sistema. Assicurati che l'utente `pi` possa eseguire il comando `reboot` senza password:

1. Modifica il file sudoers:
   ```bash
   sudo visudo
   ```

2. Aggiungi questa riga:
   ```
   pi ALL=(ALL) NOPASSWD: /sbin/reboot
   ```

## 🐛 Troubleshooting

### Il watchdog non si avvia

1. Verifica i log:
   ```bash
   journalctl -u rbp4_8gb_inverter.service -n 50
   ```

2. Controlla che il file di configurazione sia valido:
   ```bash
   python3 -c "import json; print(json.load(open('/home/pi/Python/script/Pi_Inverter/network_watchdog_config.json')))"
   ```

### Il sistema non si riavvia

1. Verifica i permessi sudo (vedi sezione Sicurezza)
2. Controlla il log del watchdog per messaggi di errore
3. Verifica che `enable_reboot` sia `true`

### Falsi positivi (riavvii non necessari)

1. Aumenta `max_failures` per dare più tempo
2. Aumenta `check_interval` per controlli meno frequenti
3. Aggiungi più host da pingare in `hosts_to_check`

## 📝 Integrazione nel Codice

Il watchdog è già integrato nello script principale `rbp4_8gb_inverter.py`:

```python
# Importazione
from classi.network_watchdog import NetworkWatchdog

# Inizializzazione
config_file = os.path.join(os.path.dirname(inverter_monitor.SCRIPT_PATH), 
                          'network_watchdog_config.json')
network_watchdog = NetworkWatchdog(
    check_interval=60,
    max_failures=10,
    ping_timeout=5,
    enable_reboot=True,
    config_file=config_file
)

# Avvio
network_watchdog.start()
```

## 📈 Statistiche

Il watchdog tiene traccia di:
- Numero totale di controlli effettuati
- Numero totale di fallimenti
- Fallimenti consecutivi correnti
- Percentuale di successo

Puoi ottenere le statistiche in qualsiasi momento:
```python
status = network_watchdog.get_status()
print(status)
```

## 🎯 Best Practices

1. **Testa prima in modalità no-reboot** con `enable_reboot: false`
2. **Monitora i log** nelle prime settimane per ottimizzare la configurazione
3. **Usa configurazione conservativa** se hai una rete instabile
4. **Aggiungi più host** se hai problemi di DNS
5. **Fai backup regolari** del sistema (indipendentemente dal watchdog)

## ❓ FAQ

**Q: Il watchdog consuma molte risorse?**  
A: No, il watchdog è molto leggero. Un ping ogni minuto consuma risorse trascurabili.

**Q: Posso usarlo con Ethernet invece che WiFi?**  
A: Sì, il watchdog funziona con qualsiasi tipo di connessione di rete.

**Q: Cosa succede se il router è offline ma internet funziona?**  
A: Il watchdog controlla anche host esterni (8.8.8.8, 1.1.1.1), quindi la connettività viene comunque verificata.

**Q: Posso fermare il watchdog senza riavviare?**  
A: Sì, imposta `"enabled": false` nel file di configurazione e riavvia il servizio.

## 📄 Licenza

Questo modulo è parte del progetto Pi_Inverter.

---

**Creato il**: 12 Novembre 2025  
**Versione**: 1.0  
**Autore**: Sistema Pi_Inverter
