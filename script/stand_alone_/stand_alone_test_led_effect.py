#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script di test per visualizzare l'effetto onda luminosa avanzato
su tutti i livelli da 1 a 8.
"""

import time
from sense_hat import SenseHat
from classi.led_controller import LEDController

def test_led_effects():
    """Test dell'effetto onda luminosa avanzato."""
    print("Inizializzazione del test LED...")
    
    # Inizializza il controller LED
    led_controller = LEDController()
    sense = SenseHat()
    
    # Definisci i colori per ogni livello (per simulare diversi rapporti di potenza)
    colors = [
        (255, 0, 0),     # Rosso (potenza molto bassa)
        (255, 64, 0),    # Arancione (potenza bassa)
        (255, 128, 0),   # Arancione-giallo (potenza medio-bassa)
        (255, 192, 0),   # Giallo (potenza media)
        (192, 255, 0),   # Giallo-verde (potenza medio-alta)
        (128, 255, 0),   # Verde chiaro (potenza alta)
        (64, 255, 64),   # Verde (potenza molto alta)
        (0, 255, 128)    # Verde-blu (potenza massima)
    ]
    
    # Parametri per durata totale del test
    total_duration = 16  # secondi
    duration_per_level = total_duration / 8  # 2 secondi per livello
    
    # Mostra ogni livello
    for level in range(1, 9):
        print(f"Mostrando livello {level}/8 - Durata: {duration_per_level} secondi")
        
        # Usa base_cycles ridotto per il test per evitare che ogni livello richieda troppo tempo
        # Usiamo max 5 cicli per ogni livello per non eccedere i 2 secondi
        # Calcoliamo i cicli in base alla durata desiderata e alla velocità dell'onda
        level_ratio = max(0.1, level / 8.0)
        wave_speed = 0.3 * (1 - 0.7 * level_ratio)  # Da 0.3 a 0.09 secondi
        max_cycles = int(duration_per_level / (wave_speed * 8))
        base_cycles = min(max_cycles, 3)  # Limita a massimo 3 cicli per livello
        
        # Mostra l'effetto
        sense.clear()
        time.sleep(0.2)  # Pausa breve tra i livelli
        led_controller.update_led_matrix(
            level=level,
            color=colors[level-1],
            base_wave_speed=0.3,  # Velocità iniziale (sarà adattata in base al livello)
            base_cycles=base_cycles
        )
    
    # Pulisci il display alla fine
    sense.clear()
    print("Test completato!")

if __name__ == "__main__":
    test_led_effects() 