#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Persistenza dati: CSV e JSON.
ZERO dipendenze da SenseHat — errori gestiti via eccezioni o print.
"""

import csv
import os
import json
from datetime import datetime, timedelta


def append_reading(filepath, timestamp, value):
    """Aggiunge una riga (timestamp, value) al file CSV."""
    try:
        with open(filepath, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, value])
    except Exception as e:
        print(f'Errore scrittura CSV {filepath}: {e}')


def read_all_values(filepath):
    """Restituisce la lista di tutti i valori (colonna 1) del CSV."""
    if not os.path.exists(filepath):
        return []

    values = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    try:
                        values.append(float(row[1]))
                    except ValueError:
                        continue
    except Exception as e:
        print(f'Errore lettura CSV {filepath}: {e}')
    return values


def read_recent_values(filepath, max_lines=500):
    """Restituisce gli ultimi N valori dal CSV (lettura efficiente tail)."""
    if not os.path.exists(filepath):
        return []

    try:
        lines = _tail_lines(filepath, max_lines)
        values = []
        for line in lines:
            parts = line.strip().split(',')
            if len(parts) >= 2:
                try:
                    values.append(float(parts[1]))
                except ValueError:
                    continue
        return values
    except Exception as e:
        print(f'Errore lettura CSV {filepath}: {e}')
        return []


def _tail_lines(filepath, n):
    """Legge le ultime N righe di un file senza caricarlo tutto in memoria."""
    with open(filepath, 'rb') as f:
        f.seek(0, 2)
        file_size = f.tell()
        if file_size == 0:
            return []

        block_size = 8192
        blocks = []
        remaining = file_size
        lines_found = 0

        while remaining > 0 and lines_found <= n:
            read_size = min(block_size, remaining)
            remaining -= read_size
            f.seek(remaining)
            block = f.read(read_size)
            blocks.append(block)
            lines_found += block.count(b'\n')

        content = b''.join(reversed(blocks)).decode('utf-8', errors='replace')
        all_lines = content.splitlines()
        return all_lines[-n:] if len(all_lines) > n else all_lines


def read_day_values(filepath, target_date, start_hour, end_hour):
    """
    Restituisce la lista di coppie (timestamp, power) per il giorno target_date,
    filtrando solo i record tra start_hour e end_hour.
    """
    if not os.path.exists(filepath):
        return []

    date_prefix = target_date.strftime('%Y_%m_%d_')
    data = []

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 2:
                    continue
                if not row[0].startswith(date_prefix):
                    continue
                try:
                    ts = datetime.strptime(row[0], '%Y_%m_%d_%H:%M')
                    if start_hour <= ts.hour < end_hour:
                        power = float(row[1])
                        data.append((ts, power))
                except (ValueError, IndexError):
                    continue
    except Exception as e:
        print(f'Errore lettura dati giornalieri da {filepath}: {e}')

    return data


def get_day_power_chart(filepath, num_bars=8, day_start_hour=6, day_end_hour=20):
    """
    Calcola i valori per il grafico a barre giornaliero (0-8 per ogni barra),
    normalizzando rispetto al 98esimo percentile storico.
    """
    now = datetime.now()
    target_date = now.date() if now.hour >= day_start_hour else (now - timedelta(days=1)).date()

    day_data = read_day_values(filepath, target_date, day_start_hour, day_end_hour)
    daylight_data = [(ts, power) for ts, power in day_data if power > 0]

    if not daylight_data:
        return [0] * num_bars

    all_values = read_all_values(filepath)
    positive_values = [v for v in all_values if v > 0]
    historical_max = _percentile(positive_values, 98) if positive_values else 1

    start_time = datetime.combine(target_date, datetime.min.time().replace(hour=day_start_hour))
    end_time = datetime.combine(target_date, datetime.min.time().replace(hour=day_end_hour))
    total_seconds = (end_time - start_time).total_seconds()

    buckets = [[] for _ in range(num_bars)]
    for ts, power in daylight_data:
        if ts < start_time or ts > end_time:
            continue
        elapsed = (ts - start_time).total_seconds()
        index = min(int((elapsed / total_seconds) * num_bars), num_bars - 1)
        buckets[index].append(power)

    if historical_max == 0:
        return [0] * num_bars

    levels = []
    for bucket in buckets:
        if bucket:
            avg = sum(bucket) / len(bucket)
            ratio = avg / historical_max
            level = 8 if ratio >= 0.9 else min(8, max(0, round(ratio * 8)))
        else:
            level = 0
        levels.append(level)

    return levels


def cleanup_csv(filepath, max_age_days=365):
    """Archivia i record piu vecchi di max_age_days e riscrive il CSV con i soli recenti."""
    if not os.path.exists(filepath):
        return

    threshold_date = datetime.now() - timedelta(days=max_age_days)

    try:
        all_data = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    try:
                        ts = datetime.strptime(row[0], '%Y_%m_%d_%H:%M')
                        power = float(row[1])
                        all_data.append((ts, power))
                    except (ValueError, IndexError):
                        continue

        old_data = [(ts, p) for ts, p in all_data if ts < threshold_date]
        recent_data = [(ts, p) for ts, p in all_data if ts >= threshold_date]

        if old_data:
            archive_path = filepath.replace('.csv', '_archive.csv')
            with open(archive_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for ts, power in old_data:
                    writer.writerow([ts.strftime('%Y_%m_%d_%H:%M'), power])
            print(f'Archiviati {len(old_data)} record in {archive_path}')

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for ts, power in recent_data:
                writer.writerow([ts.strftime('%Y_%m_%d_%H:%M'), power])

        print(f'Cleanup CSV completato: {filepath}')
    except Exception as e:
        print(f'Errore durante cleanup CSV {filepath}: {e}')


def read_daily_energy(filepath):
    """Legge il valore 'energy_kwh' dal JSON. None se assente o errore."""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
                return data.get('energy_kwh')
    except Exception as e:
        print(f'Errore lettura daily energy da {filepath}: {e}')
    return None


def save_daily_energy(filepath, energy_kwh):
    """Salva il daily yield su JSON con data e timestamp. Ritorna True/False."""
    try:
        now = datetime.now()
        data = {
            'date': now.strftime('%Y-%m-%d'),
            'energy_kwh': energy_kwh,
            'timestamp': now.strftime('%Y-%m-%d %H:%M:%S'),
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        print(f'Errore salvataggio daily energy in {filepath}: {e}')
        return False


def _percentile(values, pct):
    """Restituisce il percentile pct (0-100) di una lista di valori."""
    if not values:
        return 0
    sorted_vals = sorted(values)
    idx = int(len(sorted_vals) * pct / 100)
    return sorted_vals[min(idx, len(sorted_vals) - 1)]
