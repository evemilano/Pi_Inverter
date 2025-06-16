#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from sense_hat import SenseHat

class LEDController:
    def __init__(self):
        self.sense = SenseHat()
        self.sense.set_rotation(180)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.BLACK = (0, 0, 0)
        self.BLUE = (0, 0, 255)  # Colore per il consumo dalla rete
        self.current_grid_power = 0  # Aggiungiamo questa variabile per tracciare il valore corrente della rete

    def update_bar_chart(self, bar_values, color):
        """Aggiorna il grafico a barre sulla matrice LED."""
        pixels = []
        for y in range(8):
            row = []
            for level in bar_values:
                ratio = level / 8.0
                r = int(255 * ratio)
                g = int(255 * ratio)
                b = int(255 * (1 - ratio))
                col = (r, g, b)
                if y >= 8 - level:
                    row.append(col)
                else:
                    row.append(self.BLACK)
            pixels.extend(row)
        self.sense.set_pixels(pixels)

    def update_led_matrix(self, solar_level, grid_level, solar_color, base_wave_speed=0.3, base_cycles=20):
        """
        Crea un effetto onda luminosa avanzato con due barre verticali.
        
        - solar_level: altezza della barra solare (1-8)
        - grid_level: altezza della barra rete (1-8)
        - solar_color: colore base della barra solare
        - base_wave_speed: velocità base dell'animazione
        - base_cycles: numero base di cicli
        """
        # Adatta velocità e cicli al livello di potenza
        solar_ratio = max(0.1, solar_level / 8.0)
        grid_ratio = max(0.1, grid_level / 8.0)
        
        wave_speed = base_wave_speed * (1 - 0.7 * solar_ratio)
        cycles = int(base_cycles + (20 * solar_ratio))
        min_brightness = 0.4 - (0.2 * solar_ratio)
        
        r, g, b = solar_color
        
        for cycle in range(cycles):
            for shift in range(8):
                pixels = []
                for y in range(8):
                    # Prima barra (solare) - primi 4 pixel
                    for x in range(4):
                        if y >= 8 - solar_level:
                            relative_pos = (y - (8 - solar_level)) / solar_level
                            wave_effect = min_brightness + (1 - min_brightness) * abs((shift - 3.5) / 3.5)
                            wave_effect = wave_effect ** (1 - 0.5 * solar_ratio)
                            
                            if solar_ratio < 0.3:
                                new_r = int(r * wave_effect)
                                new_g = int((g * 0.7) * wave_effect * relative_pos)
                                new_b = int(b * wave_effect * 0.1)
                            elif solar_ratio < 0.6:
                                new_r = int(r * wave_effect * (1 - relative_pos * 0.5))
                                new_g = int(g * wave_effect)
                                new_b = int(b * wave_effect * 0.2)
                            else:
                                new_r = int(r * wave_effect * 0.3)
                                new_g = int(g * wave_effect)
                                new_b = int((b + 100) * wave_effect * relative_pos)
                            
                            pixels.append((new_r, new_g, new_b))
                        else:
                            pixels.append(self.BLACK)
                    
                    # Seconda barra (rete) - ultimi 4 pixel
                    for x in range(4):
                        if y >= 8 - grid_level:
                            relative_pos = (y - (8 - grid_level)) / grid_level
                            wave_effect = min_brightness + (1 - min_brightness) * abs((shift - 3.5) / 3.5)
                            wave_effect = wave_effect ** (1 - 0.5 * grid_ratio)
                            
                            # Colore blu per valori positivi, rosso per negativi
                            if self.current_grid_power >= 0:  # Invertiamo la condizione
                                new_r = int(0 * wave_effect)
                                new_g = int(0 * wave_effect)
                                new_b = int(255 * wave_effect)
                            else:
                                new_r = int(255 * wave_effect)
                                new_g = int(0 * wave_effect)
                                new_b = int(0 * wave_effect)
                            
                            pixels.append((new_r, new_g, new_b))
                        else:
                            pixels.append(self.BLACK)
                            
                self.sense.set_pixels(pixels)
                time.sleep(wave_speed)

    def show_message(self, message, color=None, scroll_speed=0.06):
        """Mostra un messaggio sulla matrice LED."""
        self.sense.show_message(message, text_colour=color, scroll_speed=scroll_speed)

    def calculate_level(self, current_power, historical_values):
        """Calcola il livello (da 1 a 8) per la visualizzazione del potenziometro."""
        if not historical_values:
            return 8 if current_power > 0 else 0
        
        # Separa i valori positivi e negativi dalla storia
        positive_values = [x for x in historical_values if x >= 0]
        negative_values = [x for x in historical_values if x < 0]
        
        if current_power >= 0:
            max_power = max(positive_values) if positive_values else 0
            if max_power == 0:
                return 0
            level = round((current_power / max_power) * 8)
            if level < 1 and current_power > 0:
                level = 1
        else:
            min_power = min(negative_values) if negative_values else 0
            if min_power == 0:
                return 0
            # Usiamo il valore assoluto per calcolare la proporzione
            level = round((abs(current_power) / abs(min_power)) * 8)
            if level < 1:
                level = 1
            
        return min(level, 8)

    def choose_color(self, current_power, historical_values):
        """Sceglie il colore in base alla potenza corrente rispetto al massimo storico."""
        if not historical_values:
            return self.GREEN if current_power > 0 else self.RED

        max_power = max(historical_values)
        if max_power <= 0:
            return self.RED

        ratio = current_power / max_power
        ratio = max(0, min(ratio, 1))

        if ratio < 0.5:
            r = 255
            g = int(510 * ratio)
        else:
            r = int(510 * (1 - ratio))
            g = 255

        b = 0
        return (r, g, b) 